from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource
from flask_pyoidc import OIDCAuthentication
from flask_restx._http import HTTPStatus

from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.financial_data import check_param_annee_import, parser_import, check_files_import
from app.controller.financial_data.schema_model import (
    register_financial_ae_schemamodel,
    register_financial_cp_schemamodel,
)
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication import ConnectedUser, InvalidTokenError, NoCurrentRegion
from app.servicesapp.financial_data import import_financial_data

api = Namespace(name="Engagement", path="/", description="Api de gestion des données financières de l'état")

model_financial_ae_single_api = register_financial_ae_schemamodel(api)
model_financial_cp_single_api = register_financial_cp_schemamodel(api)

auth: OIDCAuthentication = current_app.extensions["auth"]


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
    @check_param_annee_import()
    @check_files_import()
    @api.doc(security="Bearer")
    def post(self):
        """
        Charge les fichiers issus de Chorus pour enregistrer les autorisations d'engagement (AE) et les crédits de paiement (CP)
        Les lignes sont insérées de façon asynchrone
        """
        user = ConnectedUser.from_current_token_identity()
        source_region = user.current_region

        file_ae = request.files["fichierAe"]
        file_cp = request.files["fichierCp"]
        annee = int(request.form["annee"])

        import_financial_data(file_ae, file_cp, source_region, annee, user.username)
        return jsonify(
            {
                "status": 200,
                "message": "Fichiers récupérés. Demande d'import des AE et des CP en cours.",
                "source_region": source_region,
                "annee": annee,
            }
        )
