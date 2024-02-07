from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, fields
from flask_pyoidc import OIDCAuthentication
from flask_restx._http import HTTPStatus

from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.financial_data import check_param_source_annee_import, parser_import, check_files_import
from app.controller.financial_data.schema_model import (
    register_financial_ae_schemamodel,
    register_financial_cp_schemamodel,
)
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication import ConnectedUser, InvalidTokenError, NoCurrentRegion
from app.servicesapp.financial_data import import_financial_data

api = Namespace(name="Engagement", path="/", description="Api de gestion des données financières de l'état")

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


@api.route("/ae-cp")
class FinancialAe(Resource):

    @api.expect(parser_import)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_param_source_annee_import()
    @check_files_import()
    @api.doc(security="Bearer")
    def post(self):
        """
        Charge un fichier issue de Chorus pour enregistrer les lignes d'engagements
        Les lignes sont insérés de façon asynchrone
        """
        user = ConnectedUser.from_current_token_identity()
        source_region = user.current_region

        file_ae = request.files["fichierAe"]
        file_cp = request.files["fichierCp"]
        annee = int(request.form["annee"])

        task = import_financial_data(file_ae, file_cp, source_region, annee, user.username)
        return jsonify(
            {
                "status": 200,
                "message": "Fichiers récupérés. Demande d'import des AE et des CP en cours.",
                "source_region": source_region,
                "annee": annee,
                "task": task.id
            }
        )

