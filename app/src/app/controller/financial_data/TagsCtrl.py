from http import HTTPStatus
from flask import current_app, request
from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage

from app.controller.financial_data import check_file_import
from app.controller.utils.Error import ErrorController
from app.servicesapp.tags import InvalidRequest, TagsAppService


api = Namespace(
    name="Tags", path="/tags", description="API pour la manipulation des tags et leurs association aux données"
)

auth = current_app.extensions["auth"]

append_tags_input = reqparse.RequestParser()
append_tags_input.add_argument(
    "fichier", type=FileStorage, help="Fichier de tags à importer", location="files", required=True
)

appservice = TagsAppService()


@api.errorhandler(InvalidRequest)
def handle_exception(e):
    return ErrorController(e.message).to_json(), HTTPStatus.BAD_REQUEST


@api.route("/maj_ae_tags_from_export")
class TagsResource(Resource):
    @auth("openid")
    @check_file_import()
    @api.expect(append_tags_input)
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def post(self):
        """Mise à jour des tags des AE depuis un export csv"""
        input_file = request.files["fichier"]

        appservice.maj_ae_tags_from_export(input_file)
