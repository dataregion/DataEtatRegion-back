from flask import current_app, request
from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
from flask_pyoidc import OIDCAuthentication

from app.controller.financial_data import check_file_import
from app.servicesapp.tags import TagsAppService


api = Namespace(
    name="Tags", path="/tags", description="API pour la manipulation des tags et leurs association aux données"
)

auth: OIDCAuthentication = current_app.extensions["auth"]

append_tags_input = reqparse.RequestParser()
append_tags_input.add_argument(
    "fichier", type=FileStorage, help="Fichier de tags à importer", location="files", required=True
)

appservice = TagsAppService()


@api.route("/maj_ae_tags_from_export")
class TagsResource(Resource):
    # @auth.token_auth("default", scopes_required=["openid"]) # TODO: re enable
    @check_file_import()
    @api.expect(append_tags_input)
    @api.doc(security="Bearer")
    def post(self):
        """Mise à jour des tags des AE depuis un export csv"""
        input_file = request.files["fichier"]

        appservice.maj_ae_tags_from_export(input_file)
