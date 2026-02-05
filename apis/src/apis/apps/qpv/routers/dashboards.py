from http import HTTPStatus
import logging
from typing import TypeVar
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from models.connected_user import ConnectedUser
from services.shared.source_query_params import SourcesQueryParams
from services.qpv.query_params import QpvQueryParams

from apis.apps.qpv.models.dashboard_data import DashboardData
from apis.apps.qpv.services.get_data import get_dashboard_data
from apis.database import get_session_main
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()


_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_region_user(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    return params.with_update(update={"source_region": user.current_region})


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
    session: Session = Depends(get_session_main),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    params = handle_region_user(params, user)

    message = "Liste des données QPV agrégées pour les graphiques"
    data: DashboardData = await get_dashboard_data(session, params)

    return APISuccess(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=False,
        current_page=params.page,
    )
