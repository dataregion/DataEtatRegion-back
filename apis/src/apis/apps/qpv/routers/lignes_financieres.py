from http import HTTPStatus
import logging
from types import NoneType
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends
from models.entities.financial.query.FlattenFinancialLinesDataQpv import EnrichedFlattenFinancialLinesDataQPV
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesDataQpvSchema, EnrichedFlattenFinancialLinesSchema
from models.entities.financial.query import EnrichedFlattenFinancialLines

from apis.apps.qpv.models.qpv_query_params import (
    QpvQueryParams,
    SourcesQueryParams,
)
from apis.apps.qpv.services.get_colonnes import validation_colonnes
from apis.apps.qpv.services.get_data import get_annees_qpv, get_lignes
from apis.database import get_session
from models.connected_user import ConnectedUser
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.services.model.pydantic_annotation import (
    PydanticFromMarshmallowSchemaAnnotationFactory,
)
from apis.services.model.enriched_financial_lines_mappers import (
  enriched_ffl_mappers,
  enriched_ffl_pre_validation_transformer
)
from apis.shared.models import APIError, APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()

PydanticEnrichedFlattenFinancialLinesModel = PydanticFromMarshmallowSchemaAnnotationFactory[
    EnrichedFlattenFinancialLinesDataQpvSchema
].create(
    EnrichedFlattenFinancialLinesDataQpvSchema,
    custom_fields_mappers=enriched_ffl_mappers,
    pre_validation_transformer=enriched_ffl_pre_validation_transformer
)

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_national(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"
    return params


LigneFinanciere = Annotated[EnrichedFlattenFinancialLinesDataQPV, PydanticEnrichedFlattenFinancialLinesModel]


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
    print(user.current_region)
    # user_param_source_region = params.source_region
    # print(user_param_source_region)
    params = handle_national(params, user)

    # Validation des paramètres faisant référence à des colonnes
    validation_colonnes(params)

    message = "Liste des données QPV"
    data, total, has_next = get_lignes(
        session,
        params,
        additionnal_source_region=None,
    )
    print("========")
    print(data)
    print(total)
    print(has_next)

    # if len(data) == 0:
    #     print('ok')
    #     return APISuccess(
    #         code=HTTPStatus.NO_CONTENT,
    #         message="Aucun résultat ne correspond à vos critères de recherche",
    #         data=None,
    #     ).to_json_response()
    
    data = LignesFinancieres(total=total, lignes=data)
    print(data)

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
    params = handle_national(params, user)
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des années présentes dans les lignes QPV",
        data=get_annees_qpv(session, params),
    )
