from http import HTTPStatus
import logging
from types import NoneType
from typing import Annotated, Literal, TypeVar

from apis.apps.qpv.models.dashboard_data import DashboardData
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.entities.financial.query import EnrichedFlattenFinancialLines

from apis.apps.qpv.models.qpv_query_params import (
    QpvQueryParams,
    SourcesQueryParams,
)
from apis.apps.qpv.services.get_colonnes import validation_colonnes
from apis.apps.qpv.services.get_data import get_dashboard_data
from apis.database import get_session
from models.connected_user import ConnectedUser
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.services.model.pydantic_annotation import (
    PydanticFromMarshmallowSchemaAnnotationFactory,
)
from apis.services.model.enriched_financial_lines_mappers import enriched_ffl_mappers
from apis.shared.models import APIError, APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_national(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"
    return params


@router.get(
    "/147",
    summary="Récupére les lignes QPV",
    response_model=APISuccess[DashboardData],
    responses=error_responses(),
)
async def get_dashboard_data_147(
    params: QpvQueryParams = Depends(),
    session: Session = Depends(get_session),
    # user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    user = ConnectedUser({"region": "053"})
    user_param_source_region = params.source_region
    params = handle_national(params, user)

    # Validation des paramètres faisant référence à des colonnes
    validation_colonnes(params)

    message = "Liste des données QPV"
    data: DashboardData = await get_dashboard_data(session, params, "147", True)

    return APISuccess(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=False,
        current_page=params.page,
    )


@router.get(
    "/autres",
    summary="Récupére les lignes QPV",
    response_model=APISuccess[DashboardData],
    responses=error_responses(),
)
async def get_dashboard_data_147(
    params: QpvQueryParams = Depends(),
    session: Session = Depends(get_session),
    # user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    user = ConnectedUser({"region": "053"})
    user_param_source_region = params.source_region
    params = handle_national(params, user)

    # Validation des paramètres faisant référence à des colonnes
    validation_colonnes(params)

    message = "Liste des données QPV"
    data: DashboardData = await get_dashboard_data(session, params, "147", False)

    return APISuccess(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=False,
        current_page=params.page,
    )

