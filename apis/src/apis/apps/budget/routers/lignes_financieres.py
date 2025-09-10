from http import HTTPStatus
import logging
from types import NoneType
from typing import Annotated, Literal, TypeVar

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.entities.financial.query import EnrichedFlattenFinancialLines

from apis.apps.budget.models.grouped_data import GroupedData
from apis.apps.budget.models.budget_query_params import (
    FinancialLineQueryParams,
    SourcesQueryParams,
)
from apis.apps.budget.models.total import Total
from apis.apps.budget.services.get_colonnes import validation_colonnes
from apis.apps.budget.services.get_data import get_annees_budget, get_ligne, get_lignes
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

PydanticEnrichedFlattenFinancialLinesModel = PydanticFromMarshmallowSchemaAnnotationFactory[
    EnrichedFlattenFinancialLinesSchema
].create(EnrichedFlattenFinancialLinesSchema, custom_fields_mappers=enriched_ffl_mappers)

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_national(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"
    return params


LigneFinanciere = Annotated[EnrichedFlattenFinancialLines, PydanticEnrichedFlattenFinancialLinesModel]


class LignesFinancieres(BaseModel):
    type: Literal["lignes_financieres"] = "lignes_financieres"
    total: Total
    lignes: list[LigneFinanciere]


class Groupings(BaseModel):
    type: Literal["groupings"] = "groupings"
    total: Total
    groupings: list[GroupedData]


class LignesResponse(APISuccess[LignesFinancieres | Groupings | NoneType]):
    pass


class LigneResponse(APISuccess[LigneFinanciere]):
    pass


@router.get(
    "",
    summary="Récupére les lignes financières, mécanisme de grouping pour récupérer les montants agrégés",
    response_model=LignesResponse,
    responses=error_responses(),
)
def get_lignes_financieres(
    params: FinancialLineQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    user_param_source_region = params.source_region
    params = handle_national(params, user)

    # Validation des paramètres faisant référence à des colonnes
    validation_colonnes(params)

    message = "Liste des données financières"
    data, total, grouped, has_next = get_lignes(
        session,
        params,
        additionnal_source_region=user_param_source_region,
    )
    size = len(data)
    if grouped:
        message = "Liste des montants agrégés"
        data = [GroupedData(**d) for d in data]
        for d in data:
            d.colonne = params.grouping[-1].code
        data = Groupings(total=total, groupings=data)
    else:
        data = LignesFinancieres(total=total, lignes=data)

    if size == 0:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            message="Aucun résultat ne correspond à vos critères de recherche",
            data=None,
        ).to_json_response()

    return LignesResponse(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=has_next,
        current_page=params.page,
    )


@router.get(
    "/{id:int}",
    summary="Récupére les infos budgetaires en fonction de son identifiant technique",
    response_model=LigneResponse,
    responses=error_responses(),
)
def get_lignes_financieres_by_source(
    id: int,
    params: SourcesQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    if not params.source:
        return APIError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="La paramètre `source` est requis.",
        ).to_json_response()

    params = handle_national(params, user)

    ligne = get_ligne(session, params, id)
    if ligne is None:
        return APIError(
            code=HTTPStatus.NOT_FOUND,
            message="Aucun résultat ne correspond à vos critères de recherche",
        ).to_json_response()

    return LigneResponse(
        code=HTTPStatus.OK,
        message="Ligne financière",
        data=ligne,
    ).to_json_response()


@router.get(
    "/annees",
    summary="Recupère la plage des années pour lesquelles les données budgetaires courent.",
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
        message="Liste des années présentes dans les lignes financières",
        data=get_annees_budget(session, params),
    )
