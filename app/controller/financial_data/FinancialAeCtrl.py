from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, fields
from flask_pyoidc import OIDCAuthentication
from flask_restx._http import HTTPStatus

from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.financial_data import check_param_annee_import, parser_import, check_file_import
from app.controller.financial_data.schema_model import (
    register_financial_ae_schemamodel,
    register_financial_cp_schemamodel,
)
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from app.models.financial.FinancialAe import FinancialAeSchema
from app.models.financial.FinancialCp import FinancialCpSchema
from app.servicesapp.authentication import ConnectedUser, InvalidTokenError, NoCurrentRegion
from app.servicesapp.financial_data import (
    import_ae,
    search_financial_data_ae,
    get_financial_ae,
    get_financial_cp_of_ae,
    get_annees_ae,
)

api = Namespace(name="Engagement", path="/", description="Api de gestion des AE des données financières de l'état")

model_financial_ae_single_api = register_financial_ae_schemamodel(api)
model_financial_cp_single_api = register_financial_cp_schemamodel(api)

auth: OIDCAuthentication = current_app.extensions["auth"]

parser_get = get_pagination_parser(default_limit=6500)
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


@api.errorhandler(NoCurrentRegion)
def handle_no_current_region(e: NoCurrentRegion):
    return ErrorController("Aucune region n'est associée à l'utilisateur.").to_json(), HTTPStatus.BAD_REQUEST


@api.errorhandler(InvalidTokenError)
def handle_invalid_token(e: InvalidTokenError):
    return ErrorController("Token invalide.").to_json(), HTTPStatus.BAD_REQUEST


# TODO: deprecate
@api.route("/ae")
class FinancialAe(Resource):
    @api.expect(parser_import)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_param_annee_import()
    @check_file_import()
    @api.doc(security="Bearer")
    def post(self):
        """
        Charge un fichier issue de Chorus pour enregistrer les lignes d'engagements
        Les lignes sont insérés de façon asynchrone
        """
        user = ConnectedUser.from_current_token_identity()

        data = request.form

        file_ae = request.files["fichier"]
        force_update = False
        if "force_update" in data and data["force_update"] == "true":
            force_update = True

        source_region = user.current_region

        task = import_ae(file_ae, source_region, int(data["annee"]), force_update, user.username)
        return jsonify(
            {
                "status": f"Fichier récupéré. Demande d`import des engaments des données fiancières de l'état en cours (taches asynchrone id = {task.id})"
            }
        )

    @api.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        """
        Retourne les lignes d'engagements Chorus
        """
        user = ConnectedUser.from_current_token_identity()
        params = parser_get.parse_args()
        params["source_region"] = user.current_region
        page_result = search_financial_data_ae(**params)

        if page_result.items == []:
            return "", 204

        result = FinancialAeSchema(many=True).dump(page_result.items)

        return {
            "items": result,
            "pageInfo": Pagination(page_result.total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK


# TODO: deprecate
@api.route("/ae/<id>")
@api.doc(model=model_financial_ae_single_api)
class GetFinancialAe(Resource):
    """
    Récupére les infos d'engagements en fonction de son identifiant technique
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self, id: str):
        result = get_financial_ae(int(id))

        if result is None:
            return "", HTTPStatus.NO_CONTENT

        financial_ae = FinancialAeSchema().dump(result)

        return financial_ae, HTTPStatus.OK


@api.route("/ae/<id>/cp")
@api.doc(model=fields.List(fields.Nested(model_financial_cp_single_api)))
class GetFinancialCpOfAe(Resource):
    """
    Récupére les infos d'engagements en fonction de son identifiant technique
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self, id: str):
        result = get_financial_cp_of_ae(int(id))

        if result is None:
            return "", 204

        financial_cp = FinancialCpSchema(many=True).dump(result)

        return financial_cp, 200


# TODO: deprecate
@api.route("/ae/annees")
class GetYears(Resource):
    """
    Récupére la liste de toutes les années pour lesquelles on a des montants (engagés ou payés)
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        annees = get_annees_ae()
        if annees is None:
            return "", HTTPStatus.NO_CONTENT
        return annees, HTTPStatus.OK


@api.route("/ae/healthcheck")
class GetHealthcheck(Resource):
    def get(self):
        """
        Effectue un GET pour vérifier la disponibilité de l'API engagements
        """
        result_q = search_financial_data_ae(limit=10, page_number=0)
        result = FinancialAeSchema(many=True).dump(result_q.items)

        assert len(result) == 10, "On devrait récupérer 10 AE"

        return HTTPStatus.OK
