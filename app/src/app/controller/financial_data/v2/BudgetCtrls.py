from flask import current_app
from flask_pyoidc import OIDCAuthentication
from app.controller.financial_data.schema_model import register_flatten_financial_lines_schemamodel
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from models.value_objects.common import DataType
from app.servicesapp.authentication.connected_user import ConnectedUser
from app.servicesapp.financial_data import get_annees_budget, get_ligne_budgetaire, search_lignes_budgetaires, search_lignes_budgetaires_qpv

from flask_restx import Namespace, Resource, fields

from http import HTTPStatus

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema

api_ns = Namespace(name="Budget", path="/", description="Api d'accès aux données budgetaires.")
auth: OIDCAuthentication = current_app.extensions["auth"]

model_flatten_budget_schemamodel = register_flatten_financial_lines_schemamodel(api_ns)

parser_get = get_pagination_parser(default_limit=6500)
parser_get.add_argument("n_ej", type=str, action="split", help="Le numéro EJ")
parser_get.add_argument("source", type=str, help="Source de la donnée")
parser_get.add_argument("code_programme", type=str, action="split", help="le code programme (BOP)")
parser_get.add_argument("niveau_geo", type=str, help="le niveau géographique")
parser_get.add_argument(
    "code_geo",
    type=str,
    action="split",
    help="Le code d'une commune (5 chiffres), "
    "le numéro de département (2 caractères), "
    "le code epci (9 chiffres), "
    "le code d'arrondissement (3 ou 4 chiffres)"
    "ou le crte (préfixé par 'crte-')",
)
parser_get.add_argument("ref_qpv", type=int, help="Année du référentiel du QPV")
parser_get.add_argument("code_qpv", type=str, action="split", help="Les codes de QPV")
parser_get.add_argument(
    "theme", type=str, action="split", help="Le libelle theme (si code_programme est renseigné, le theme est ignoré)."
)
parser_get.add_argument("siret_beneficiaire", type=str, action="split", help="Code siret d'un beneficiaire.")
parser_get.add_argument("types_beneficiaires", type=str, action="split", help="Types de bénéficiaire.")
parser_get.add_argument("annee", type=int, action="split", help="L'année comptable.")
parser_get.add_argument("centres_couts", type=str, action="split", help="Le(s) code(s) des centres de coût")
parser_get.add_argument("domaine_fonctionnel", type=str, action="split", help="Le(s) code(s) du domaine fonctionnel.")
parser_get.add_argument(
    "referentiel_programmation", type=str, action="split", help="Le(s) code(s) du référentiel de programmation."
)
parser_get.add_argument("tags", type=str, action="split", help="Le(s) tag(s) à inclure", required=False)

pagination_model = api_ns.schema_model("Pagination", Pagination.definition_jsonschema)
paginated_budget = api_ns.model(
    "PaginatedBudgetLines",
    {
        "items": fields.List(fields.Nested(model_flatten_budget_schemamodel)),
        "pageInfo": fields.Nested(pagination_model),
    },
)


@api_ns.route("/budget")
class BudgetCtrl(Resource):
    @api_ns.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api_ns.doc(security="Bearer")
    @api_ns.response(HTTPStatus.NO_CONTENT, "Aucune lignes correspondante")
    @api_ns.response(HTTPStatus.OK, description="Lignes correspondante", model=paginated_budget)
    def get(self):
        """Recupère les lignes de données budgetaires génériques"""
        user = ConnectedUser.from_current_token_identity()
        params = parser_get.parse_args()
        params["source_region"] = user.current_region
        data_source_mapping = current_app.config.get("DATA_SOURCE_MAPPING", {})
        params["data_source"] = data_source_mapping.get(user.current_region)

        page_result = search_lignes_budgetaires(**params)
        result = EnrichedFlattenFinancialLinesSchema(many=True).dump(page_result.items)

        if len(page_result.items) == 0:
            return "", HTTPStatus.NO_CONTENT

        total = page_result.total if page_result.total is not None else 0

        return {
            "items": result,
            "pageInfo": Pagination(total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK


@api_ns.route("/budget/data-qpv")
class BudgetQPVCtrl(Resource):
    @api_ns.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api_ns.doc(security="Bearer")
    @api_ns.response(HTTPStatus.NO_CONTENT, "Aucune lignes correspondante")
    @api_ns.response(HTTPStatus.OK, description="Lignes correspondante", model=paginated_budget)
    def get(self):
        """Recupère les lignes de données budgetaires génériques"""
        user = ConnectedUser.from_current_token_identity()
        params = parser_get.parse_args()
        params["source_region"] = user.current_region
        data_source_mapping = current_app.config.get("DATA_SOURCE_MAPPING", {})
        params["data_source"] = data_source_mapping.get(user.current_region)

        page_result = search_lignes_budgetaires_qpv(**params)
        result = EnrichedFlattenFinancialLinesSchema(many=True).dump(page_result.items)

        if len(page_result.items) == 0:
            return "", HTTPStatus.NO_CONTENT

        total = page_result.total if page_result.total is not None else 0

        return {
            "items": result,
            "pageInfo": Pagination(total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK


@api_ns.route("/budget/<source>/<id>")
class GetBudgetCtrl(Resource):
    """
    Récupére les infos budgetaires en fonction de son identifiant technique
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api_ns.doc(security="Bearer")
    @api_ns.response(HTTPStatus.NO_CONTENT, "Aucune ligne correspondante")
    @api_ns.response(HTTPStatus.OK, description="Ligne correspondante", model=model_flatten_budget_schemamodel)
    def get(self, source: DataType, id: str):
        user = ConnectedUser.from_current_token_identity()
        source_region = user.current_region

        id_i = int(id)
        ligne = get_ligne_budgetaire(source, id_i, source_region)

        if ligne is None:
            return "", HTTPStatus.NO_CONTENT

        ligne_payload = EnrichedFlattenFinancialLinesSchema().dump(ligne)
        return ligne_payload, HTTPStatus.OK


@api_ns.route("/budget/annees")
class GetPlageAnnees(Resource):
    """
    Recupère la plage des années pour lesquelles les données budgetaires courent.
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api_ns.doc(security="Bearer")
    @api_ns.response(HTTPStatus.OK, description="Liste des années", model=fields.List(fields.Integer))
    def get(self):
        user = ConnectedUser.from_current_token_identity()
        source_region = user.current_region

        annees = get_annees_budget(source_region)
        if annees is None:
            return [], HTTPStatus.OK
        return annees, HTTPStatus.OK


@api_ns.route("/budget/healthcheck")
class GetHealthcheck(Resource):
    def get(self):
        """
        Effectue un GET pour vérifier la disponibilité de l'API des lignes budgetaires
        """
        result_q = search_lignes_budgetaires(limit=10, page_number=0, source_region="053")
        result = EnrichedFlattenFinancialLinesSchema(many=True).dump(result_q.items)

        assert len(result) == 10, "On devrait récupérer 10 lignes budgetaires"

        return HTTPStatus.OK
