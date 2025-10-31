import logging

from models.connected_user import ConnectedUser

from fastapi import APIRouter, Depends
from apis.apps.apis_externes.models import ApiExterneError
from apis.apps.apis_externes.services.data_subventions import InfoApiSubvention, subvention
from apis.security.keycloak_token_validator import KeycloakTokenValidator

logger = logging.getLogger(__name__)

keycloak_validator = KeycloakTokenValidator.get_application_instance()
router = APIRouter()

@router.get(
    "/{siret}",
    response_model=InfoApiSubvention,
    responses={
        500: {
            "model": ApiExterneError,
        }
    }
)
def get_info_subvention(
    siret: str,
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    response = subvention(siret)
    return response
