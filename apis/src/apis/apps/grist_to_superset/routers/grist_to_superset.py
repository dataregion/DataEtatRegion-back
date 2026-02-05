from http import HTTPStatus
from io import BytesIO
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, status
import pandas as pd
import json
import logging
from models.value_objects.to_superset import ColumnIn
from sqlalchemy.orm import Session

from apis.apps.grist_to_superset.exceptions.import_data_exceptions import UserNotFoundException
from apis.apps.grist_to_superset.models.publish_response import PublishResponse
from apis.apps.grist_to_superset.services.import_data_from_grist import ImportService
from apis.database import get_session_main
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.security.security_header import verify_api_key
from apis.shared.exceptions import BadRequestError
from models.connected_user import ConnectedUser
from supersetcli.services.superset_api import SupersetApiService
from supersetcli.services.errors import UserNotFound
from apis.config.current import get_config


router = APIRouter()
logger = logging.getLogger(__name__)

keycloak_validator = KeycloakTokenValidator.get_application_instance()


@router.get(
    "/user/check",
    dependencies=[Depends(verify_api_key)],
    summary="Vérifier l'existence d'un utilisateur Superset",
    description="Endpoint public pour vérifier si un utilisateur existe dans Superset et récupérer son ID.",
)
async def check_user_exists(
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """
    Vérifie si l'utilisateur connecté existe dans Superset.

    Requiert un token JWT valide.

    Returns:
        {
            "exists": bool,
            "user_id": int | None,
        }
    """
    try:
        config = get_config()
        superset_config = config.to_superset_config
        superset_service = SupersetApiService(
            server=superset_config.url_superset,
            username=superset_config.user_superset_tech_login,
            password=superset_config.user_superset_tech_password,
        )

        # Utiliser l'email de l'utilisateur connecté comme username
        username = user.email
        user_id = superset_service.get_user_id_by_username(username)

        if user_id:
            logger.info(f"User '{username}' found in Superset with ID: {user_id}")
            return {
                "exists": True,
                "user_id": user_id,
            }
        else:
            logger.info(f"User '{username}' not found in Superset")
            return {
                "exists": False,
                "user_id": None,
            }

    except UserNotFound as e:
        logger.error(f"Error checking user '{user.email}' in Superset: {str(e)}")
        return {
            "exists": False,
            "user_id": None,
        }


@router.post(
    "/link-superset",
    dependencies=[Depends(verify_api_key)],
    summary="Créer le dataset dans Superset",
    description="Endpoint sécurisé Créer le dataset côté Superset.",
)
async def link_superset(
    table_id: str = Form(..., description="Identifiant de la table cible"),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """
    Crée un dataset dans Superset.

    Requiert un token API valide dans le header X-API-Key.
    """

    logger.info(f"Link Superset requested by user '{user.email}' for the table '{table_id}'")
    try:
        config = get_config()
        superset_config = config.to_superset_config
        superset_service = SupersetApiService(
            server=superset_config.url_superset,
            username=superset_config.user_superset_tech_login,
            password=superset_config.user_superset_tech_password,
        )
        username = user.email
        user_id = superset_service.get_user_id_by_username(username)

        if user_id:
            dataset_id = superset_service.get_or_create_dataset(
                database_id=superset_config.superset_database_id,
                schema=superset_config.db_schema_export,
                table_name=table_id,
                catalog=superset_config.superset_catalog,
            )
            superset_service.set_dataset_owners(dataset_id=dataset_id, owner_ids=[user_id])
            return HTTPStatus.OK
        else:
            raise UserNotFoundException()
    except Exception as e:
        logger.error(f"Error initializing Superset service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la connexion à Superset.",
        )


@router.post(
    "/import/table",
    response_model=PublishResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Importer les données CSV avec schéma de colonnes",
    description="Endpoint sécurisé pour importer des données CSV avec schéma de colonnes (provenant de Grist).",
)
async def import_table_data(
    file: UploadFile = File(..., description="Fichier CSV à importer contenant les données"),
    table_id: str = Form(..., description="Identifiant de la table cible"),
    columns: str = Form(..., description="Schéma des colonnes au format JSON"),
    session: Session = Depends(get_session_main),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """
    Importe des données CSV dans le système.

    Requiert un token API valide dans le header X-API-Key.
    """
    # Vérifier que c'est bien un CSV
    if file.filename and not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format CSV",
        )

    # Parser le schéma des colonnes
    columns_list = json.loads(columns)
    columns_schema = [ColumnIn(**col) for col in columns_list]

    logger.info(
        f"Import de l'utilisateur '{user.email}' demandé pour la table '{table_id}' avec {len(columns_schema)} colonnes"
    )

    # Lire le CSV
    contents = file.file.read()
    data = BytesIO(contents)
    df = pd.read_csv(data)

    logger.info(f"CSV lu: {len(df)} lignes, {len(df.columns)} colonnes")

    # Valider que les colonnes du schéma existent dans le CSV
    csv_columns = set(df.columns)
    schema_columns = {col.id for col in columns_schema}

    missing_columns = schema_columns - csv_columns
    if missing_columns:
        raise BadRequestError(
            code=HTTPStatus.BAD_REQUEST,
            api_message=f"Colonnes manquantes dans le CSV: {', '.join(missing_columns)}",
        )

    # Filtrer le DataFrame pour ne garder que les colonnes du schéma
    df_filtered = df[[col.id for col in columns_schema]]

    import_service = ImportService(session)

    rows_imported = import_service.import_table(
        table_id=table_id,
        dataframe=df_filtered,
        columns_schema=columns_schema,
        schema_name=get_config().to_superset_config.db_schema_export,
    )

    data.close()
    file.file.close()
    return PublishResponse(
        success=True,
        message=f"Import réussi de {rows_imported} lignes",
        table_id=table_id,
        rows_imported=len(df_filtered),
    )
