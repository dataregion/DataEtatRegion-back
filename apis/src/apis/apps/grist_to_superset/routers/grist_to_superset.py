from http import HTTPStatus
from io import BytesIO
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, status
import pandas as pd
import json
import logging
from models.value_objects.to_superset import ColumnIn
from sqlalchemy.orm import Session

from apis.apps.grist_to_superset.models.publish_response import PublishResponse
from apis.apps.grist_to_superset.services.import_data_from_grist import ImportService
from apis.database import get_session
from apis.security.security_header import verify_api_key
from apis.shared.exceptions import BadRequestError

router = APIRouter()
logger = logging.getLogger(__name__)


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
    session: Session = Depends(get_session),
):
    """
    Importe des données CSV dans le système.

    Requiert un token API valide dans le header X-API-Key.
    """

    # Vérifier que c'est bien un CSV
    if file.filename and not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier doit être au format CSV")

    # Parser le schéma des colonnes
    columns_list = json.loads(columns)
    columns_schema = [ColumnIn(**col) for col in columns_list]

    logger.info(f"Import demandé pour la table '{table_id}' avec {len(columns_schema)} colonnes")

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
    rows_imported = import_service.import_table(table_id=table_id, dataframe=df_filtered, columns_schema=columns_schema)

    data.close()
    file.file.close()
    return PublishResponse(
        success=True,
        message=f"Import réussi de {rows_imported} lignes",
        table_id=table_id,
        rows_imported=len(df_filtered),
    )
