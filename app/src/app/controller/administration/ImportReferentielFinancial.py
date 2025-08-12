"""
Controller permettant de mettre à jours certains référentiels des données fiancières à partir d'un fichier 'calculette

"""

from flask import current_app, request, jsonify
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage

from app.controller.Decorators import check_permission
from app.exceptions.exceptions import FileNotAllowedException
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication.connected_user import connected_user_from_current_token_identity
from app.services.import_refs import import_ref_calculette


api = Namespace(
    name="Referentiel", path="/referentiels", description="API de de mise à jours des référentiels issue de Chorus"
)

auth = current_app.extensions["auth"]

parser = reqparse.RequestParser()
parser.add_argument("fichier", type=FileStorage, help="Fichier calculette", location="files", required=True)


@api.route("")
class TaskRunImportRef(Resource):
    @auth("openid")
    @check_permission(AccountRole.ADMIN)
    @api.doc(security="Bearer")
    @api.expect(parser)
    def post(self):
        user = connected_user_from_current_token_identity()
        file_ref = request.files["fichier"]

        try:
            import_ref_calculette(file_ref, user.username)
            return jsonify({"status": "Fichier récupéré. Demande d`import du referentiel en cours"})
        except FileNotAllowedException as e:
            return {"status": e.message}, HTTPStatus.BAD_REQUEST
