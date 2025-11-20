import logging
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form, status
from pydantic import ValidationError
from grist_plugins.settings import Settings

# Modèles importés depuis models/to_superset.py
from grist_plugins.models.to_superset import ColumnIn
import time


logger = logging.getLogger(__name__)
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)
router = APIRouter()

# Charger les settings
settings = Settings()


@router.get("/to-superset", response_class=HTMLResponse)
async def to_superset_page(request: Request):
    logger.info("GET /to-superset - Affichage de la page de sélection de colonne.")
    # Déterminer le chemin du JS selon l'environnement
    js_path = (
        "http://localhost:5173/static/js/to-superset.js" if settings.dev_mode else "/static/dist/js/to-superset.min.js"
    )
    return templates.TemplateResponse("/to_superset.html", {"request": request, "jsPath": js_path})


@router.post("/to-superset/publish")
async def publish(file: UploadFile = File(...), tableId: str = Form(...), columns: str = Form(...)):
    # Parser et valider les colonnes avec Pydantic
    try:
        columns_list = [ColumnIn(**col) for col in json.loads(columns)]
    except (json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid columns format: {str(e)}")

    logger.info(f"POST /to-superset/publish - Publication pour la table '{tableId}'")
    logger.info(f"Colonnes validées : {columns_list}")

    logger.info(f"POST /to-superset/publish - Publication pour la table '{tableId}'")
    try:
        # Lire le fichier CSV
        contents = await file.read()
        csv_content = contents.decode("utf-8")
        logger.info(f"Fichier CSV reçu : {file.filename}, taille : {len(csv_content)} bytes")

        # Validation : il doit y avoir au moins une colonne indexée
        has_index = any(col.is_index for col in columns_list)
        if not has_index:
            logger.warning("Validation échouée : aucune colonne indexée.")
            return JSONResponse(
                {"success": False, "message": "Veuillez sélectionner au moins une colonne comme index."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Validation réussie pour la table : '{tableId}' avec {len(columns_list)} colonne(s)")
        # TODO, envoyer vers Data Etat Api la création de la table + insert données
        time.sleep(4)  # Simuler un délai de traitement
        return {"success": True, "message": f"Table '{tableId}' et colonnes validées."}

    except json.JSONDecodeError as err:
        logger.error(f"Erreur JSON pour les colonnes : {err}")
        return JSONResponse(
            {"success": False, "message": "Format JSON invalide pour les colonnes"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as err:
        logger.error(f"Erreur lors de la validation : {err}")
        return JSONResponse({"success": False, "message": str(err)}, status_code=status.HTTP_400_BAD_REQUEST)
