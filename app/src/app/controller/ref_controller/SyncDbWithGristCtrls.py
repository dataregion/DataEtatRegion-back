import logging
from app.clients.grist.factory import GristConfiguationException
from app.controller.Decorators import authM2M
from app.controller.utils.Error import ErrorController
from app.servicesapp.grist import ParsingColumnsError
from flask import current_app, request
from flask_restx import Namespace, Resource
from http import HTTPStatus

from gristcli.gristservices.errors import ApiGristError
from app.tasks.refs.sync_with_grist import init_referentiels_from_grist, sync_referentiels_from_grist


logger = logging.getLogger()


api_ns = Namespace(
    name="SyncDbWithGrist", path="/sync-referentiels", description="Api pour synchroniser la DB avec Grist"
)
auth = current_app.extensions["auth"]


@api_ns.errorhandler(ApiGristError)
def handle_exception_grist(e: ApiGristError):
    message = e.call_error_description.description
    return ErrorController(f"Erreur lors de l'API à GRIST : {message}").to_json(), e.call_error_description.code


@api_ns.errorhandler(ParsingColumnsError)
def handle_exception_parsing_columns(e: ParsingColumnsError):
    return ErrorController(e.message).to_json(), HTTPStatus.BAD_REQUEST


config_grist = current_app.config.get("GRIST", {})


@api_ns.route("")
class SyncThemesWithGrist(Resource):

    @authM2M(config_grist.get("TOKEN_SYNC_DB", None))
    @api_ns.doc(security="Bearer")
    @api_ns.response(201, "Success")
    @api_ns.response(400, "Bad request")
    @api_ns.response(403, "Forbidden")
    def post(self):
        """Récupère les données du doc Grist référentiels et synchronise les tables de référentiels"""
        doc_id = request.args.get("docId")
        table_id = request.args.get("tableId")
        table_name = request.args.get("tableName", None)
        if table_name is None:
            table_name = f"{doc_id}_{table_id}"

        # TODO : Flag feature V0.2
        if table_name != "ref_theme" and table_name != "ref_code_programme":
            logger.error(f"[GRIST] Synchronization not implemented for table {table_name}")
            raise GristConfiguationException()

        token_user = config_grist.get("TOKEN_SCIM", None)
        if token_user is None:
            logger.error("[GRIST] Missing TOKEN_SCIM in GRIST configuration")
            raise GristConfiguationException()

        init_referentiels_from_grist.delay(token_user, doc_id, table_id, table_name)

        return HTTPStatus.CREATED

    @authM2M(config_grist.get("TOKEN_SYNC_DB", None))
    @api_ns.doc(security="Bearer")
    @api_ns.response(201, "Success")
    @api_ns.response(400, "Bad request")
    @api_ns.response(403, "Forbidden")
    def put(self):
        """Récupère les données du doc Grist référentiels et synchronise les tables de référentiels"""
        doc_id = request.args.get("docId")
        table_id = request.args.get("tableId")
        table_name = request.args.get("tableName", None)
        if table_name is None:
            table_name = f"{doc_id}_{table_id}"

        # TODO : Flag feature V0.2
        if table_name != "ref_theme" and table_name != "ref_code_programme":
            logger.error(f"[GRIST] Synchronization not implemented for table {table_name}")
            raise GristConfiguationException()

        token_user = config_grist.get("TOKEN_SCIM", None)
        if token_user is None:
            logger.error("[GRIST] Missing TOKEN_SCIM in GRIST configuration")
            raise GristConfiguationException()

        sync_referentiels_from_grist.delay(token_user, doc_id, table_id, table_name)

        return HTTPStatus.CREATED
