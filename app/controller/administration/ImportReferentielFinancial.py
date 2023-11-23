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
from app.servicesapp.authentication import ConnectedUser
from app.services.import_refs import import_ref_calculette
from app.tasks.refs.update_ref_communes import import_file_pvd_from_website # noqa: F401
from app.tasks.tags.apply_tags import apply_tags_pvd # noqa: F401


api = Namespace(
    name="Referentiel", path="/referentiels", description="API de de mise à jours des référentiels issue de Chorus"
)

auth = current_app.extensions["auth"]

parser = reqparse.RequestParser()
parser.add_argument("fichier", type=FileStorage, help="Fichier calculette", location="files", required=True)


@api.route("")
class TaskRunImportRef(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission(AccountRole.ADMIN)
    @api.doc(security="Bearer")
    @api.expect(parser)
    def post(self):
        user = ConnectedUser.from_current_token_identity()
        file_ref = request.files["fichier"]

        try:
            import_ref_calculette(file_ref, user.username)
            return jsonify({"status": "Fichier récupéré. Demande d`import du referentiel en cours"})
        except FileNotAllowedException as e:
            return {"status": e.message}, HTTPStatus.BAD_REQUEST


# @api.route("/communes-pvd")
# class TaskRunImportRefPVD(Resource):
#     @auth.token_auth("default", scopes_required=["openid"])
#     @check_permission(AccountRole.ADMIN)
#     @api.doc(security="Bearer")
#     def get(self):
#         import_file_pvd_from_website.delay("https://www.data.gouv.fr/fr/datasets/r/2a5a9898-1b6c-457c-b67e-032b0a0c7b8a")


# @api.route("/apply-pvd")
# class TaskRunImportRefPVDApply(Resource):
#     @auth.token_auth("default", scopes_required=["openid"])
#     @check_permission(AccountRole.ADMIN)
#     @api.doc(security="Bearer")
#     def get(self):
#         apply_tags_pvd.delay("pvd", None)
