from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, reqparse
from marshmallow_jsonschema import JSONSchema
from werkzeug.datastructures import FileStorage

from app.controller.Decorators import check_permission
from app.controller.financial_data import check_file_import
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from app.models.financial.Ademe import AdemeSchema
from app.services.authentication.connected_user import ConnectedUser
from app.services.financial_data import import_ademe, search_ademe, get_ademe

api = Namespace(name="Ademe", path='/',
                description='Api de gestion des données ADEME')

auth = current_app.extensions['auth']

parser_get = get_pagination_parser(default_limit=5000)


parser_import_file = reqparse.RequestParser()
parser_import_file.add_argument('fichier', type=FileStorage, help="fichier à importer", location='files', required=True)


@api.route('/france-2030')
class France2030Import(Resource):

    @api.expect(parser_import_file)
    @auth.token_auth('default', scopes_required=['openid'])
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_file_import()
    @api.doc(security="Bearer")
    def post(self):
        """
        Charge un fichier issue de l'excel France 2030
        Les lignes sont insérés de manière asynchrone
        """
        user = ConnectedUser.from_current_token_identity()

        file_ademe = request.files['fichier']

        task = import_ademe(file_ademe, user.username)
        return jsonify({"status": f'Fichier récupéré. Demande d`import des  données ADEME en cours (taches asynchrone id = {task.id}'})

    @api.expect(parser_get)
    @auth.token_auth('default', scopes_required=['openid'])
    @api.doc(security="Bearer")
    def get(self):
        """
        Retourne les lignes de financement France 2030
        """
        # TODO
        return {'items': [],
                'pageInfo': Pagination(0, 1, 0).to_json()}, 200

