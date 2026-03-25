import logging
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, BinaryIO, Generator
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form, status, Header
from pydantic import ValidationError
from grist_plugins.settings import SettingsDep
from models.value_objects.to_superset import ColumnIn
from grist_plugins.services.to_superset import get_superset_service
from grist_plugins.services.utils import async_wrap_sync_cm
from services.antivirus import AntivirusService, VirusFoundError

logger = logging.getLogger(__name__)
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)
router = APIRouter()


################################################################
# Méthodes pour le scan antivirus sur les fichiers uploadés
@contextmanager
def _scan_file_stream_or_raise(
    settings: SettingsDep,
    file: UploadFile,
    endpoint: str,
    source: str,
) -> Generator[BinaryIO, None, None]:
    if not settings.antivirus.enabled:
        logger.warning(
            "Antivirus désactivé source=%s endpoint=%s filename=%s",
            source,
            endpoint,
            file.filename,
        )
        yield file.file
        return

    av_service = AntivirusService(
        host=settings.antivirus.host,
        port=settings.antivirus.port,
        timeout=settings.antivirus.timeout,
        max_file_size_bytes=settings.antivirus.max_file_size_bytes,
    )

    context = {
        "source": source,
        "endpoint": endpoint,
        "filename": file.filename or "upload.csv",
    }
    with av_service.scanned_binary_io(file.file, context=context) as scanned_input_io:
        yield scanned_input_io


################################################################


@router.get("/callback", response_class=HTMLResponse)
async def callback_oidc(request: Request, settings: SettingsDep):
    logger.info("GET /callback - Affichage de la page de sélection de colonne.")
    # Déterminer le chemin du JS selon l'environnement
    js_path = (
        "http://localhost:5173/static/js/to-superset.js" if settings.dev_mode else "/static/dist/js/to-superset.min.js"
    )
    return templates.TemplateResponse("/login/callback_oidc.html", {"request": request, "jsPath": js_path})


@router.get("/to-superset", response_class=HTMLResponse)
async def to_superset_page(request: Request, settings: SettingsDep):
    logger.info("GET /to-superset - Affichage de la page de sélection de colonne.")
    # Déterminer le chemin du JS selon l'environnement
    js_path = (
        "http://localhost:5173/static/js/to-superset.js" if settings.dev_mode else "/static/dist/js/to-superset.min.js"
    )
    # Sérialiser la config OIDC en JSON pour l'utiliser en JS
    oidc_config = {
        "url": settings.keycloak.url,
        "realm": settings.keycloak.realm,
        "clientId": settings.keycloak.client_id,
    }
    return templates.TemplateResponse(
        "/to_superset.html",
        {"request": request, "jsPath": js_path, "oidc": oidc_config, "url_superset": settings.url_superset},
    )


@router.post("/to-superset/publish")
async def publish(
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
    file: UploadFile = File(...),
    tableId: str = Form(...),
    columns: str = Form(...),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header manquant")

    token = authorization.replace("Bearer ", "")
    logger.info(f"Token reçu: {token[:10]}...")

    # Initialiser le service
    superset_dataetat_service = get_superset_service(settings.url_to_superset_api, settings.url_token_to_superset)
    user_exists = await superset_dataetat_service.check_user_exists(token)
    if not user_exists:
        logger.error("L'utilisateur ne s'est jamais connecté à Superset")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Vous n'avez pas de compte sur Superset actuellement. "
                "Veuillez vous connecter une première fois à Superset avant d'importer des données. "
                "Si vous n'avez pas accès, contactez l'administrateur de la plateforme."
            ),
        )

    # Parser et valider les colonnes avec Pydantic
    logger.info(f"POST /to-superset/publish - Publication pour la table '{tableId}'")
    try:
        columns_list = [ColumnIn(**col) for col in json.loads(columns)]
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid columns format: {str(e)}")

    logger.debug(f"Colonnes validées : {columns_list}")

    try:
        logger.info(f"Validation réussie pour la table : '{tableId}' avec {len(columns_list)} colonne(s)")

        cm = _scan_file_stream_or_raise(
            settings=settings,
            file=file,
            endpoint="/to-superset/publish",
            source="grist_plugins.to_superset.publish",
        )
        a_cm = async_wrap_sync_cm(cm)
        async with a_cm as scanned_file_stream:
            # Appel à l'API d'import distante
            result = await superset_dataetat_service.import_table(
                token=token,
                file=scanned_file_stream,
                table_id=tableId,
                columns_json=columns,
            )
        return {
            "success": True,
            "message": result.get("message", f"Table '{tableId}' importée avec succès"),
            "table_id": tableId,
            "rows_imported": result.get("rows_imported", 0),
        }
    except HTTPException:
        # Les HTTPException du service sont déjà formatées
        raise
    except json.JSONDecodeError as err:
        logger.error(f"Erreur JSON pour les colonnes : {err}")
        return JSONResponse(
            {"success": False, "message": "Format JSON invalide pour les colonnes"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except VirusFoundError as e:
        logging.error("Fichier infecté détecté.", exc_info=e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Le fichier a été refusé car il est infecté par un virus.",
            },
        )
    except Exception as err:
        logger.error(f"Erreur inattendue lors de la publication : {err}")
        return JSONResponse(
            {
                "success": False,
                "message": "Erreur inattendue lors de la publication. Merci de contacter votre Administrateur",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/to-superset/link")
async def link(
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
    tableId: str = Form(...),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header manquant")

    token = authorization.replace("Bearer ", "")
    try:
        superset_dataetat_service = get_superset_service(settings.url_to_superset_api, settings.url_token_to_superset)

        await superset_dataetat_service.link_to_superset(
            token=token,
            table_id=tableId,
        )
        return {
            "success": True,
            "message": "Liens Superset réalisé",
        }
    except HTTPException:
        # Les HTTPException du service sont déjà formatées
        raise
    except Exception as err:
        logger.error(f"Erreur inattendue lors du liens avec Superset : {err}")
        return JSONResponse(
            {
                "success": False,
                "message": "Erreur inattendue lors du liens avec superset. Les données ont bien été importé dans la plateforme, mais nous n'avons pas pu établir le liens avec Superset."
                "Merci de contacter votre Administrateur",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
