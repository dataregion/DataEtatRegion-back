from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, fields, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage

from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.financial_data import (
    check_file_import,
    check_param_annee_import,
    parser_import,
    check_files_import,
)
from app.controller.financial_data.schema_model import register_financial_cp_schemamodel
from app.models.enums.AccountRole import AccountRole
from models.schemas.financial import FinancialCpSchema
from app.servicesapp import WerkzeugFileStorage
from app.servicesapp.authentication.connected_user import connected_user_from_current_token_identity
from models.exceptions import InvalidTokenError, NoCurrentRegion
from app.servicesapp.financial_data import (
    get_financial_cp_of_ae,
    import_financial_data,
    import_national_data,
    do_import_qpv_lieu_action,
)

api = Namespace(name="Engagement", path="/", description="Api de gestion des données financières de l'état")

model_financial_cp_single_api = register_financial_cp_schemamodel(api)

auth = current_app.extensions["auth"]


@api.errorhandler(NoCurrentRegion)
def handle_no_current_region(e: NoCurrentRegion):
    return ErrorController("Aucune region n'est associée à l'utilisateur.").to_json(), HTTPStatus.BAD_REQUEST


@api.errorhandler(InvalidTokenError)
def handle_invalid_token(e: InvalidTokenError):
    return ErrorController("Token invalide.").to_json(), HTTPStatus.BAD_REQUEST


@api.route("/region")
class LoadFinancialDataRegion(Resource):
    @api.expect(parser_import)
    @auth("openid")
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
        user = connected_user_from_current_token_identity()
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
    @api.expect(parser_import)
    @auth("openid")
    @check_permission([AccountRole.COMPTABLE_NATIONAL])
    @check_files_import()
    @check_param_annee_import()
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def post(self):
        """
        Charge les fichiers issus de Chorus pour enregistrer les autorisations d'engagement (AE) et les crédits de paiement (CP) au niveau National.
        Les lignes sont insérées de façon asynchrone
        """
        user = connected_user_from_current_token_identity()
        client_id = user.azp

        file_ae: WerkzeugFileStorage = WerkzeugFileStorage(request.files["fichierAe"])
        file_cp: WerkzeugFileStorage = WerkzeugFileStorage(request.files["fichierCp"])
        annee = int(request.form["annee"])

        import_national_data(file_ae, file_cp, annee, user.username, client_id=client_id)
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

    @auth("openid")
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def get(self, id: str):
        result = get_financial_cp_of_ae(int(id))

        if result is None:
            return "", 204

        financial_cp = FinancialCpSchema(many=True).dump(result)

        return financial_cp, 200


parser_import_file = reqparse.RequestParser()
parser_import_file.add_argument("fichier", type=FileStorage, help="fichier à importer", location="files", required=True)


@api.route("/qpv-lieu-action")
class QpvLieuActionCtrl(Resource):
    @api.expect(parser_import_file)
    @auth("openid")
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_file_import()
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def post(self):
        """
        Charge un fichier faisant le lien entre QPV et AE
        Les lignes sont insérés de manière asynchrone
        """
        file_qpv_lieu_action = request.files["fichier"]
        flow_run = do_import_qpv_lieu_action(file_qpv_lieu_action)
        return jsonify(
            {
                "status": f"Fichier récupéré. Demande d`import des données QPVLieuAction en cours (taches asynchrone id = {flow_run.id}"
            }
        )
