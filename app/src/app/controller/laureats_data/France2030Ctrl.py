import dataclasses

from flask import jsonify, current_app, request, abort
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage

from app.controller.Decorators import check_permission
from app.controller.financial_data import check_file_import
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication.connected_user import connected_user_from_current_token_identity
from app.servicesapp.france2030 import (
    SousAxePlanRelancePayload,
    StructurePayload,
    liste_axes_france2030,
    search_france_2030,
    search_france_2030_beneficiaire,
    import_france_2030,
)

api = Namespace(name="France2030", path="/", description="Api de gestion des données France 2030")


auth = current_app.extensions["auth"]

parser_get = get_pagination_parser(default_limit=6500)
parser_get.add_argument("structures", type=str, action="split", help="Noms des structures")
parser_get.add_argument("axes", type=str, action="split", help="Axes")
parser_get.add_argument("niveau_geo", type=str, help="le niveau géographique")
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


parser_import_file = reqparse.RequestParser()
parser_import_file.add_argument("fichier", type=FileStorage, help="fichier à importer", location="files", required=True)
parser_import_file.add_argument("annee", type=int, help="Année du fichier france 2030", location="files", required=True)


@api.route("/france-2030")
class France2030Import(Resource):
    @api.expect(parser_import_file)
    @auth("openid")
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_file_import()
    @api.doc(security="Bearer")
    def post(self):
        """
        Charge un fichier issue de l'excel France 2030
        Les lignes sont insérés de manière asynchrone
        """
        data = request.form
        user = connected_user_from_current_token_identity()
        annee = int(data["annee"])

        file_france2030 = request.files["fichier"]

        task = import_france_2030(file_france2030, annee=annee, username=user.username)
        return jsonify(
            {
                "status": f"Fichier récupéré. Demande d`import des données FRANCE2030 en cours (taches asynchrone id = {task.id}"
            }
        )

    @api.expect(parser_get)
    @auth("openid")
    @api.doc(security="Bearer")
    def get(self):
        """
        Retourne les lignes de financement France 2030
        """
        params = parser_get.parse_args()

        try:
            search = search_france_2030(**params)
        except NotImplementedError as e:
            abort(501, str(e))

        return {
            "items": search.items,
            "pageInfo": Pagination(search.total, search.page, search.per_page).to_json(),
        }, HTTPStatus.OK


#############################################
# XXX: A terme, ce devra être des référentiels
#
parser_searchterm = reqparse.RequestParser()
parser_searchterm.add_argument("term", type=str, help="The search term")


@api.route("/france-2030-axes")
class France2030Axes(Resource):
    @auth("openid")
    @api.doc(security="Bearer")
    def get(self) -> list[SousAxePlanRelancePayload]:
        axes = liste_axes_france2030()
        payload = [dataclasses.asdict(x) for x in axes]
        return payload  # type: ignore


@api.route("/france-2030-structures")
class France2030Structures(Resource):
    @auth("openid")
    @api.expect(parser_searchterm)
    @api.doc(security="Bearer")
    def get(self) -> list[StructurePayload]:
        params = parser_searchterm.parse_args()
        print(params)

        structures = search_france_2030_beneficiaire(params["term"])
        return [dataclasses.asdict(x) for x in structures]  # type: ignore


@api.route("/france-2030-territoires")
class France2030Territoires(Resource):
    # TODO: implementer
    @auth("openid")
    @api.expect(parser_searchterm)
    @api.doc(security="Bearer")
    def get(self) -> list[StructurePayload]:
        abort(501, "France 2030 ne supporte pas encore les territoires.")
