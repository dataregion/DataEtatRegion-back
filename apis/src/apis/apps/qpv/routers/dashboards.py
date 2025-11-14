from http import HTTPStatus
import logging
from typing import TypeVar

from apis.apps.qpv.models.dashboard_data import DashboardData
from apis.shared.query_builder import SourcesQueryParams
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.apps.qpv.models.qpv_query_params import QpvQueryParams
from apis.apps.qpv.services.get_colonnes import validation_colonnes
from apis.apps.qpv.services.get_data import get_dashboard_data
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


class DashboardResponse(APISuccess[DashboardData]):
    pass


@router.get(
    "",
    summary="Récupére les lignes QPV agrégées pour les graphiques",
    response_model=DashboardResponse,
    responses=error_responses(),
)
async def get_dashboard(
    params: QpvQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    handle_region_user(params, user)
    # Validation des paramètres faisant référence à des colonnes
    validation_colonnes(params)

    message = "Liste des données QPV agrégées pour les graphiques"
    data: DashboardData = await get_dashboard_data(session, params)

    return APISuccess(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=False,
        current_page=params.page,
    )
