from http import HTTPStatus
import logging
from types import NoneType
from typing import Annotated, TypeVar
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.connected_user import ConnectedUser
from models.entities.financial.query.FlattenFinancialLinesDataQpv import FlattenFinancialLinesDataQPV
from models.schemas.financial import FlattenFinancialLinesDataQpvSchema
from services.shared.source_query_params import SourcesQueryParams
from services.qpv.query_params import QpvQueryParams

from apis.apps.qpv.services.get_data import get_annees_qpv, get_lignes
from apis.database import get_session
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.services.model.pydantic_annotation import make_pydantic_annotation_from_marshmallow_lignes
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()

PydanticFlattenFinancialLinesModel = make_pydantic_annotation_from_marshmallow_lignes(
    FlattenFinancialLinesDataQpvSchema, False
)


_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_region_user(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    return params.with_update(update={"source_region": user.current_region})


LigneFinanciere = Annotated[FlattenFinancialLinesDataQPV, PydanticFlattenFinancialLinesModel]


class LignesFinancieres(BaseModel):
    lignes: list[LigneFinanciere]


class LignesResponse(APISuccess[LignesFinancieres | NoneType]):
    pass


@router.get(
    "",
    summary="Récupére les lignes QPV",
    response_model=LignesResponse,
    responses=error_responses(),
)
def get_lignes_financieres(
    params: QpvQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    params = handle_region_user(params, user)

    message = "Liste des données QPV"
    data, has_next = get_lignes(
        session,
        params,
        additionnal_source_region=None,
    )

    data = LignesFinancieres(total=None, lignes=data)

    return LignesResponse(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=has_next,
        current_page=params.page,
    )


@router.get(
    "/annees",
    summary="Recupère la plage des années pour lesquelles les données QPV courent.",
    response_model=APISuccess[list[int]],
    responses=error_responses(),
)
def get_annees(
    params: SourcesQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    params = handle_region_user(params, user)
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des années présentes dans les lignes QPV",
        data=get_annees_qpv(session, params),
    )
