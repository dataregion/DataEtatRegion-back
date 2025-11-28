import logging
import json
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form, status, Header
import httpx
from pydantic import ValidationError
from grist_plugins.settings import SettingsDep
from models.value_objects.to_superset import ColumnIn

logger = logging.getLogger(__name__)
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)
router = APIRouter()


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
        "clientId": settings.keycloak.client_id
    }
    return templates.TemplateResponse("/to_superset.html", {"request": request, "jsPath": js_path, "oidc": oidc_config})


@router.post("/to-superset/publish")
async def publish(
    settings: SettingsDep,authorization: Annotated[str | None, Header()] = None,  file: UploadFile = File(...), tableId: str = Form(...), columns: str = Form(...)
):
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header manquant")
    
    token = authorization.replace("Bearer ", "")
    logger.info(f"Token reçu: {token[:10]}...")

    # Parser et valider les colonnes avec Pydantic
    logger.info(f"POST /to-superset/publish - Publication pour la table '{tableId}'")
    try:
        columns_list = [ColumnIn(**col) for col in json.loads(columns)]
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid columns format: {str(e)}")

    logger.debug(f"Colonnes validées : {columns_list}")

    try:
        # Lire le fichier CSV
        file_content = await file.read()
        # Validation : il doit y avoir au moins une colonne indexée
        has_index = any(col.is_index for col in columns_list)
        if not has_index:
            logger.warning("Validation échouée : aucune colonne indexée.")
            return JSONResponse(
                {"success": False, "message": "Veuillez sélectionner au moins une colonne comme index."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifier que le fichier n'est pas vide
        if not file_content:
            logger.error("Fichier CSV vide")
            return JSONResponse(
                content={"success": False, "message": "Le fichier CSV est vide"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Validation réussie pour la table : '{tableId}' avec {len(columns_list)} colonne(s)")

        # Appel à l'API d'import distante
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Envoi vers l'API d'import Grist: {settings.url_to_superset_api}")

            response = await client.post(
                settings.url_to_superset_api,
                files={"file": (file.filename or f"{tableId}.csv", file_content, "text/csv")},
                data={
                    "table_id": tableId,
                    "columns": columns,  # On renvoie le JSON tel quel
                },
                headers={"X-API-Key": settings.url_token_to_superset, "Authorization": f"Bearer {token}"},
            )

            # Gestion des erreurs HTTP
            if response.status_code == 403:
                logger.error("Erreur d'authentification avec l'API d'import")
                return JSONResponse(
                    content={"success": False, "message": "Erreur d'authentification avec l'API de destination"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if response.status_code == 400:
                error_data = response.json()
                logger.error(f"Erreur de validation côté API: {error_data}")
                return JSONResponse(
                    content={"success": False, "message": error_data.get("detail", "Erreur de validation des données")},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text

                logger.error(f"Erreur API ({response.status_code}): {error_detail}")
                return JSONResponse(
                    content={"success": False, "message": f"Erreur lors de l'import: {error_detail}"},
                    status_code=response.status_code,
                )

            # Succès - Parser la réponse
            result = response.json()
            logger.info(f"Import réussi: {result.get('rows_imported', 0)} lignes importées")

            return {
                "success": True,
                "message": result.get("message", f"Table '{tableId}' importée avec succès"),
                "table_id": tableId,
                "rows_imported": result.get("rows_imported", 0),
            }

    except json.JSONDecodeError as err:
        logger.error(f"Erreur JSON pour les colonnes : {err}")
        return JSONResponse(
            {"success": False, "message": "Format JSON invalide pour les colonnes"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as err:
        logger.error(f"Erreur lors de la validation : {err}")
        return JSONResponse({"success": False, "message": str(err)}, status_code=status.HTTP_400_BAD_REQUEST)
