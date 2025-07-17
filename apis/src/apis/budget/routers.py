from http import HTTPStatus
from typing import Annotated

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema

from fastapi import APIRouter, Depends, Request

from models.dtos.budget_query_params import BudgetQueryParams
from services.authentication.connected_user import ConnectedUser
from services.utilities.observability import SummaryOfTimePerfCounter

from apis.budget.servicesapp import (
    get_list_colonnes_grouping,
    get_list_colonnes_tableau,
    get_query_params,
    get_results,
)
from apis.utils.annotations import handle_exceptions
from apis.utils.models import APISuccess

from apis.config import config
from apis import auth


router = APIRouter()


@router.get("/healthcheck")
@handle_exceptions
def ofe():
    with SummaryOfTimePerfCounter.cm("hc_search_lignes_budgetaires"):
        result_q = get_list_colonnes_tableau(
            limit=10, page_number=0, source_region="053"
        )

    with SummaryOfTimePerfCounter.cm("hc_serialize_lignes_budgetaires"):
        result = EnrichedFlattenFinancialLinesSchema(many=True).dump(result_q["items"])

    assert len(result) == 10, "On devrait récupérer 10 lignes budgetaires"

    return HTTPStatus.OK


@router.get("/colonnes")
@handle_exceptions
def get_colonnes_tableau():
    return APISuccess(
        status_code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le tableau",
        data=get_list_colonnes_tableau(),
    ).to_json_response()


@router.get("/grouping")
@handle_exceptions
def get_colonnes_grouping():
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le grouping",
        data=get_list_colonnes_grouping(),
    ).to_json_response()


@router.get("")
@handle_exceptions
# @auth("openid")
def get_lignes_financieres(request: Request):

    params: BudgetQueryParams = get_query_params(request)

    user = ConnectedUser.from_current_token_identity()
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"

    message, data, has_next = get_results(params)
    data = EnrichedFlattenFinancialLinesSchema(many=True).dump(data)

    if len(data) == 0:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            message="Aucun résultat ne correspond à vos critères de recherche",
            data=[],
        )

    api_response = APISuccess(code=HTTPStatus.OK, message=message, data=data)
    api_response.set_pagination(params.page, has_next)
    return api_response


# @api_ns.route("/budget/<source>/<id>")
# class GetBudgetCtrl(Resource):
#     """
#     Récupére les infos budgetaires en fonction de son identifiant technique
#     :return:
#     """

#     @auth("openid")
#     @api_ns.doc(security="OAuth2AuthorizationCodeBearer")
#     @api_ns.response(HTTPStatus.NO_CONTENT, "Aucune ligne correspondante")
#     @api_ns.response(HTTPStatus.OK, description="Ligne correspondante", model=model_flatten_budget_schemamodel)
#     def get(self, source: DataType, id: str):
#         user = ConnectedUser.from_current_token_identity()
#         source_region = None
#         data_source = None
#         if user.current_region != "NAT":
#             source_region = user.current_region
#         else:
#             data_source = "NATION"

#         id_i = int(id)
#         ligne = get_ligne_budgetaire(source, id_i, source_region, data_source)

#         if ligne is None:
#             return "", HTTPStatus.NO_CONTENT

#         ligne_payload = EnrichedFlattenFinancialLinesSchema().dump(ligne)
#         return ligne_payload, HTTPStatus.OK


# @api_ns.route("/budget/annees")
# class GetPlageAnnees(Resource):
#     """
#     Recupère la plage des années pour lesquelles les données budgetaires courent.
#     """

#     @auth("openid")
#     @api_ns.doc(security="OAuth2AuthorizationCodeBearer")
#     @api_ns.response(HTTPStatus.OK, description="Liste des années", model=fields.List(fields.Integer))
#     def get(self):
#         user = ConnectedUser.from_current_token_identity()
#         source_region = None
#         data_source = None
#         if user.current_region != "NAT":
#             source_region = user.current_region
#         else:
#             data_source = "NATION"

#         annees = get_annees_budget(source_region, data_source)
#         if annees is None:
#             return [], HTTPStatus.OK
#         return annees, HTTPStatus.OK


# @router.get("/users")
# @handle_exceptions
# def get(self):
#     """
#     Effectue un GET pour vérifier la disponibilité de l'API des lignes budgetaires
#     """
#     with SummaryOfTimePerfCounter.cm("hc_search_lignes_budgetaires"):
#         result_q = search_lignes_budgetaires(limit=10, page_number=0, source_region="053")

#     with SummaryOfTimePerfCounter.cm("hc_serialize_lignes_budgetaires"):
#         result = EnrichedFlattenFinancialLinesSchema(many=True).dump(result_q["items"])

#     assert len(result) == 10, "On devrait récupérer 10 lignes budgetaires"

#     return HTTPStatus.OK
