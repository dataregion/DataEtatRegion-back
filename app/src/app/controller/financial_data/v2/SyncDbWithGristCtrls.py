import logging
from app.clients.grist.factory import GristConfiguationException
from app.controller.Decorators import authM2M
from app.controller.utils.Error import ErrorController
from app.services.grist.__init_ import ParsingColumnsError
from flask import current_app
from flask_restx import Namespace, Resource
from http import HTTPStatus

from gristcli.gristservices.errors import ApiGristError
from app.tasks.refs.sync_with_grist import sync_referentiels_from_grist


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
class SyncRefWithGrist(Resource):
    @authM2M(config_grist.get("TOKEN_SYNC_DB", None))
    @api_ns.doc(security="Bearer")
    @api_ns.response(201, "Success")
    @api_ns.response(400, "Bad request")
    @api_ns.response(403, "Forbidden")
    def post(self):
        """Récupère les données du doc Grist référentiels et synchronise les tables de référentiels"""

        tech_user = config_grist.get("TECH_USER", None)
        doc_id = config_grist.get("REFERENTIELS_DOC_ID", None)

        if tech_user is None or doc_id is None:
            logger.error("[GRIST] Missing TECH_USER or REFERENTIELS_DOC_ID in GRIST configuration")
            raise GristConfiguationException()

        sync_referentiels_from_grist.delay(tech_user, doc_id)

        return HTTPStatus.CREATED
