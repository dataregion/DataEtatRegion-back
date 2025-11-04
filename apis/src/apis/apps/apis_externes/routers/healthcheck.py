import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from apis.apps.apis_externes.services.entreprise import retrieve_entreprise_info

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    "entreprise-batch",
    summary="Vérification de la disponibilité de l'API Entreprise en mode batch",
)
def entreprise_batch_healthcheck():
    # Siret NumihFrance
    try:
        siret = "18310021300028"
        entreprise = retrieve_entreprise_info(siret, use_batch=True)

        assert entreprise.donnees_etablissement.siret == siret
        return JSONResponse(status_code=200, content={"status": "ok"})
    except Exception as e:
        logger.error("Entreprise batch healthcheck failed", exc_info=e)
        return JSONResponse(status_code=500, content={"status": "failed"})
