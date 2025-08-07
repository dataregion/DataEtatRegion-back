from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from apis.apps.budget.services.get_colonnes import (
    get_list_colonnes_grouping,
    get_list_colonnes_tableau,
)
from apis.config.current import get_config
from apis.database import get_db
from apis.security.connected_user import ConnectedUser
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess
from apis.shared.openapi_config import build_api_success_response


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator(get_config())


@router.get(
    "/tableau",
    summary="Liste des colonnes possibles pour le tableau",
    response_class=JSONResponse,
    responses=build_api_success_response(is_list=True),
)
@handle_exceptions
def get_colonnes_tableau(
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    db: Session = Depends(get_db),
):
    logger.debug("[COLONNES] Récupération des colonnes pour le tableau")
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le tableau",
        data=[c.to_dict() for c in get_list_colonnes_tableau()],
    )


@router.get(
    "/grouping",
    summary="Liste des colonnes possibles pour le grouping",
    response_class=JSONResponse,
    responses=build_api_success_response(is_list=True),
)
@handle_exceptions
def get_colonnes_grouping(
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    db: Session = Depends(get_db),
):
    logger.debug("[COLONNES] Récupération des colonnes pour le grouping")
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le grouping",
        data=[c.to_dict() for c in get_list_colonnes_grouping()],
    )
