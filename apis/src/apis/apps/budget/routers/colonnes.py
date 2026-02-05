from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.value_objects.colonne import Colonnes
from services.budget.colonnes import (
    get_list_colonnes_grouping,
    get_list_colonnes_tableau,
)
from apis.database import get_session_main
from models.connected_user import ConnectedUser
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.models import APISuccess

from apis.exception_handlers import error_responses


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()


@router.get(
    "/tableau",
    summary="Liste des colonnes possibles pour le tableau",
    response_model=APISuccess[Colonnes],
    responses=error_responses(),
)
def get_colonnes_tableau(
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
    session: Session = Depends(get_session_main),
):
    logger.debug("[COLONNES] Récupération des colonnes pour le tableau")
    response = APISuccess[Colonnes](
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le tableau",
        data=get_list_colonnes_tableau(),
    )
    return response


@router.get(
    "/grouping",
    summary="Liste des colonnes possibles pour le grouping",
    response_model=APISuccess[Colonnes],
    responses=error_responses(),
)
def get_colonnes_grouping(
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
    session: Session = Depends(get_session_main),
):
    logger.debug("[COLONNES] Récupération des colonnes pour le grouping")
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le grouping",
        data=get_list_colonnes_grouping(),
    )
