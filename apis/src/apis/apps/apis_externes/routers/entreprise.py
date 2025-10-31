import logging
from models.connected_user import ConnectedUser
from fastapi import APIRouter, Depends

from apis.apps.apis_externes.models import ApiExterneError
from apis.apps.apis_externes.services.entreprise import retrieve_entreprise_info
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from services.apis_externes.models.InfoApiEntreprise import InfoApiEntreprise

logger = logging.getLogger(__name__)


keycloak_validator = KeycloakTokenValidator.get_application_instance()
router = APIRouter()

@router.get(
    "/{siret}",
    response_model=InfoApiEntreprise,
    responses={
        500: {
            "model": ApiExterneError,
        }
    }
)
def get_info_entreprise(
    siret: str,
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    """
    Récupère les informations d'une entreprise à partir de son SIRET.
    """
    return retrieve_entreprise_info(siret)

