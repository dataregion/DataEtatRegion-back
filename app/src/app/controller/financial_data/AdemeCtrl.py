from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage

from app.controller.Decorators import check_permission
from app.controller.financial_data import check_file_import
from app.controller.financial_data.schema_model import register_ademe_schemamodel
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from models.schemas.financial import AdemeSchema
from app.servicesapp.authentication import ConnectedUser
from app.servicesapp.financial_data import import_ademe, search_ademe, get_ademe


api = Namespace(name="Ademe", path="/", description="Api de gestion des données ADEME")

model_ademe_single_api = register_ademe_schemamodel(api)

auth = current_app.extensions["auth"]

parser_get = get_pagination_parser(default_limit=6500)
parser_get.add_argument("niveau_geo", type=str, help="Le niveau géographique")
parser_get.add_argument(
    "code_geo",
    type=str,
    action="split",
    help="Le code d'une commune (5 chiffres), "
    "le numéro de département (2 caractères), "
    "le code epci (9 chiffres), "
    "le code d'arrondissement (3 ou 4 chiffres)"
    "ou le crte (préfixé par 'crte-')",
)
parser_get.add_argument("siret_beneficiaire", type=str, action="split", help="Code siret d'un beneficiaire")
parser_get.add_argument("annee", type=int, action="split", help="L'année comptable")

parser_import_file = reqparse.RequestParser()
parser_import_file.add_argument("fichier", type=FileStorage, help="fichier à importer", location="files", required=True)

parser_get.add_argument("tags", type=str, action="split", help="Le(s) tag(s) à inclure", required=False)


@api.route("/ademe")
class AdemeImport(Resource):
    @api.expect(parser_import_file)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_file_import()
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def post(self):
        """
        Charge un fichier issue de l'ADEME
        Les lignes sont insérés de manière asynchrone
        """
        user = ConnectedUser.from_current_token_identity()

        file_ademe = request.files["fichier"]

        task = import_ademe(file_ademe, user.username)
        return jsonify(
            {
                "status": f"Fichier récupéré. Demande d`import des  données ADEME en cours (taches asynchrone id = {task.id}"
            }
        )

    @api.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def get(self):
        """
        Retourne les lignes de financement ADEME
        """
        params = parser_get.parse_args()
        page_result = search_ademe(**params)

        if page_result.items == []:
            return "", 204

        result = AdemeSchema(many=True).dump(page_result.items)

        return {
            "items": result,
            "pageInfo": Pagination(page_result.total, page_result.page, page_result.per_page).to_json(),
        }, HTTPStatus.OK


@api.route("/ademe/<id>")
@api.doc(model=model_ademe_single_api)
class GetAdemeByid(Resource):
    """
    Récupére les infos d'une dépense ADEME
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="OAuth2AuthorizationCodeBearer")
    def get(self, id: str):
        result = get_ademe(int(id))

        if result is None:
            return "", HTTPStatus.NO_CONTENT

        financial_ae = AdemeSchema().dump(result)

        return financial_ae, HTTPStatus.OK
