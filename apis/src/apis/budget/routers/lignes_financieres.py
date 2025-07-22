from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema

from apis.budget.dtos.grouped_data import GroupedData
from apis.database import get_db
from apis.budget.dtos.budget_query_params import BudgetQueryParams
from apis.budget.servicesapp import get_annees_budget, get_list_colonnes_grouping, get_results
from apis.security import ConnectedUser
from apis.utils.annotations import handle_exceptions
from apis.utils.models import APISuccess


router = APIRouter()

@router.get("/lignes")
@handle_exceptions
# @auth("openid")
# def get_lignes_financieres(params: BudgetQueryParams = Depends(), user: ConnectedUser = Depends(get_connected_user), db: Session = Depends(get_db)):
def get_lignes_financieres(params: BudgetQueryParams = Depends(), db: Session = Depends(get_db)):

    user: ConnectedUser = ConnectedUser({"region": "053"})
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"

    # Mapping colonnes grouping
    if params.grouping is not None:
        params.map_colonnes(get_list_colonnes_grouping())

    message, data, grouped, has_next = get_results(db, params)
    if grouped:
        data = [GroupedData(**d) for d in data]
    else:
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


@router.get("/annees")
@handle_exceptions
# @auth("openid")
# def get_lignes_financieres(params: BudgetQueryParams = Depends(), user: ConnectedUser = Depends(get_connected_user), db: Session = Depends(get_db)):
def get_annees(params: BudgetQueryParams = Depends(), db: Session = Depends(get_db)):
    """
    Recupère la plage des années pour lesquelles les données budgetaires courent.
    """

    user = ConnectedUser.from_current_token_identity()
    source_region = None
    data_source = None
    if user.current_region != "NAT":
        source_region = user.current_region
    else:
        data_source = "NATION"

    annees = get_annees_budget(source_region, data_source)
    return APISuccess(code=HTTPStatus.OK, message="Liste des années présentes dans les lignes financières", data=annees)



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
