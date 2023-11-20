from http import HTTPStatus
from flask import current_app
from flask_restx import Namespace, Resource
from flask_pyoidc import OIDCAuthentication
from app.controller.financial_data.schema_model import register_flatten_financial_lines_schemamodel

from app.controller.utils.ControllerUtils import get_pagination_parser

from app.models.common.Pagination import Pagination
from app.models.financial.query import EnrichedFlattenFinancialLinesSchema
from app.servicesapp.authentication.connected_user import ConnectedUser
from app.servicesapp.financial_data import search_financial_lines


api_ns = Namespace(name="Budget", path="/", description="Api de  gestion des AE des données financières de l'état")

auth: OIDCAuthentication = current_app.extensions["auth"]

model_flatten_budget_schemamodel = register_flatten_financial_lines_schemamodel(api_ns)

parser_get = get_pagination_parser(default_limit=5000)
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
parser_get.add_argument(
    "theme", type=str, action="split", help="Le libelle theme (si code_programme est renseigné, le theme est ignoré)."
)
parser_get.add_argument("siret_beneficiaire", type=str, action="split", help="Code siret d'un beneficiaire.")
parser_get.add_argument("types_beneficiaires", type=str, action="split", help="Types de bénéficiaire.")
parser_get.add_argument("annee", type=int, action="split", help="L'année comptable.")
parser_get.add_argument("domaine_fonctionnel", type=str, action="split", help="Le(s) code(s) du domaine fonctionnel.")
parser_get.add_argument(
    "referentiel_programmation", type=str, action="split", help="Le(s) code(s) du référentiel de programmation."
)
parser_get.add_argument("tags", type=str, action="split", help="Le(s) tag(s) à inclure", required=False)


@api_ns.route("/budget")
class BudgetCtrl(Resource):
    @api_ns.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api_ns.doc(security="Bearer")
    def get(self):
        """Recupère les lignes de données budgetaires génériques"""
        user = ConnectedUser.from_current_token_identity()
        params = parser_get.parse_args()
        params["source_region"] = user.current_region

        page_result = search_financial_lines(**params)
        result = EnrichedFlattenFinancialLinesSchema(many=True).dump(page_result.items)

        if len(page_result.items) == 0:
            return "", 204

        return {
            "items": result,
            "pageInfo": Pagination(page_result.total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK
