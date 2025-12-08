from http import HTTPStatus
import logging
from types import NoneType
from typing import TypeVar

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.connected_user import ConnectedUser
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.value_objects.grouped_data import GroupedData
from services.budget.query_params import BudgetQueryParams
from services.shared.source_query_params import SourcesQueryParams

from apis.apps.budget.routers.api_models import Groupings, LigneFinanciere, LignesFinancieres
from apis.apps.budget.services.get_data import get_annees_budget, get_ligne, get_lignes
from apis.database import get_session
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.services.model.pydantic_annotation import make_pydantic_annotation_from_marshmallow_lignes
from apis.shared.models import APIError, APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()

PydanticEnrichedFlattenFinancialLinesModel = make_pydantic_annotation_from_marshmallow_lignes(
    EnrichedFlattenFinancialLinesSchema, True
)

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_national(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    if user.current_region != "NAT":
        params = params.with_update(update={"source_region": user.current_region})
    else:
        params = params.with_update(update={"data_source": "NATION"})
    return params


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
    params: BudgetQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    force_no_cache: bool = False,
):
    user_param_source_region = params.source_region
    params = handle_national(params, user)

    message = "Liste des données financières"
    data, total, grouped, has_next = get_lignes(
        session,
        params,
        additionnal_source_region=user_param_source_region,
        force_no_cache=force_no_cache,
    )
    size = len(data)
    if grouped:
        message = "Liste des montants agrégés"
        data = [GroupedData(**d) for d in data]
        for d in data:
            d.colonne = params.grouping_list[-1].code
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


def _get_user() -> ConnectedUser:
    return ConnectedUser(
        {
            "email": "benjamin.bagot@sib.fr",
            "username": "benjamin.bagot@sib.fr",
            "region": "053",
        }
    )
