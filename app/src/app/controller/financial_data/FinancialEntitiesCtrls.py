from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, fields
from flask_pyoidc import OIDCAuthentication
from flask_restx._http import HTTPStatus

from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.financial_data import (
    check_param_annee_import,
    parser_import_region,
    parser_import_nation,
    check_files_import,
)
from app.controller.financial_data.schema_model import register_financial_cp_schemamodel
from app.models.enums.AccountRole import AccountRole
from models.schemas.financial import FinancialCpSchema
from app.servicesapp import WerkzeugFileStorage
from app.servicesapp.authentication import ConnectedUser
from app.servicesapp.exceptions.authentication import InvalidTokenError, NoCurrentRegion
from app.servicesapp.financial_data import get_financial_cp_of_ae, import_financial_data, import_national_data

api = Namespace(name="Engagement", path="/", description="Api de gestion des données financières de l'état")

model_financial_cp_single_api = register_financial_cp_schemamodel(api)

auth: OIDCAuthentication = current_app.extensions["auth"]


@api.errorhandler(NoCurrentRegion)
def handle_no_current_region(e: NoCurrentRegion):
    return ErrorController("Aucune region n'est associée à l'utilisateur.").to_json(), HTTPStatus.BAD_REQUEST


@api.errorhandler(InvalidTokenError)
def handle_invalid_token(e: InvalidTokenError):
    return ErrorController("Token invalide.").to_json(), HTTPStatus.BAD_REQUEST


@api.route("/region")
class LoadFinancialDataRegion(Resource):
    @api.expect(parser_import_region)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_param_annee_import()
    @check_files_import()
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def post(self):
        """
        Charge les fichiers issus de Chorus pour enregistrer les autorisations d'engagement (AE) et les crédits de paiement (CP) au niveau Régional.
        Les lignes sont insérées de façon asynchrone

        La region est récupérer depuis les attributs de l'utilisateur connecté
        """
        user = ConnectedUser.from_current_token_identity()
        client_id = user.azp
        source_region = user.current_region

        file_ae: WerkzeugFileStorage = WerkzeugFileStorage(request.files["fichierAe"])
        file_cp: WerkzeugFileStorage = WerkzeugFileStorage(request.files["fichierCp"])
        annee = int(request.form["annee"])

        import_financial_data(file_ae, file_cp, source_region, annee, user.username, client_id=client_id)
        return jsonify(
            {
                "status": 200,
                "message": "Fichiers récupérés. Demande d'import des AE et des CP en cours.",
                "source_region": source_region,
                "annee": annee,
            }
        )


@api.route("/national")
class LoadFinancialDataNation(Resource):
    @api.expect(parser_import_nation)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission([AccountRole.COMPTABLE_NATIONAL])
    @check_files_import()
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def post(self):
        """
        Charge les fichiers issus de Chorus pour enregistrer les autorisations d'engagement (AE) et les crédits de paiement (CP) au niveau National.
        Les lignes sont insérées de façon asynchrone
        """
        user = ConnectedUser.from_current_token_identity()
        client_id = user.azp

        file_ae: WerkzeugFileStorage = WerkzeugFileStorage(request.files["fichierAe"])
        file_cp: WerkzeugFileStorage = WerkzeugFileStorage(request.files["fichierCp"])

        import_national_data(file_ae, file_cp, user.username, client_id=client_id)
        return jsonify(
            {"status": 200, "message": "Fichiers récupérés. Demande d'import des EJ et des DP national en cours."}
        )


@api.route("/ae/<id>/cp")
@api.doc(model=fields.List(fields.Nested(model_financial_cp_single_api)))
class GetFinancialCpOfAe(Resource):
    """
    Récupére les infos d'engagements en fonction de son identifiant technique
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def get(self, id: str):
        result = get_financial_cp_of_ae(int(id))

        if result is None:
            return "", 204

        financial_cp = FinancialCpSchema(many=True).dump(result)

        return financial_cp, 200
