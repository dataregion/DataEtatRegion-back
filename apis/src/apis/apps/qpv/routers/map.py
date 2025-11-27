from http import HTTPStatus
import logging
from typing import TypeVar

from apis.apps.qpv.models.map_data import MapData
from services.query_builders.source_query_params import SourcesQueryParams
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.apps.qpv.models.qpv_query_params import QpvQueryParams
from apis.apps.qpv.services.get_colonnes import validation_colonnes
from apis.apps.qpv.services.get_data import get_map_data
from apis.database import get_session
from models.connected_user import ConnectedUser
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_region_user(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    params.source_region = user.current_region
    return params


class MapResponse(APISuccess[MapData]):
    pass


@router.get(
    "",
    summary="Récupére les lignes QPV agrégées pour la cartographie",
    response_model=MapResponse,
    responses=error_responses(),
)
async def get_map(
    params: QpvQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    handle_region_user(params, user)
    # Validation des paramètres faisant référence à des colonnes
    validation_colonnes(params)

    message = "Liste des données QPV agrégées pour la cartographie"
    data: MapData = await get_map_data(session, params)

    return APISuccess(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=False,
        current_page=params.page,
    )
