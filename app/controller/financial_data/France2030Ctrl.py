import dataclasses

from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage

from app.controller.Decorators import check_permission
from app.controller.financial_data import check_file_import
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication import ConnectedUser
from app.servicesapp.financial_data import import_france_2030

api = Namespace(name="France2030", path="/", description="Api de gestion des données France 2030")

auth = current_app.extensions["auth"]

parser_get = get_pagination_parser(default_limit=5000)
parser_get.add_argument("structures", type=str, action="split", help="Noms des structures")
parser_get.add_argument("sous-axes", type=str, action="split", help="Sous axes")
parser_get.add_argument("territoires", type=str, action="split", help="Territoires (communes)")


parser_import_file = reqparse.RequestParser()
parser_import_file.add_argument("fichier", type=FileStorage, help="fichier à importer", location="files", required=True)
parser_import_file.add_argument("annee", type=int, help="Année du fichier france 2030", location="files", required=True)


@api.route("/france-2030")
class France2030Import(Resource):
    @api.expect(parser_import_file)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission([AccountRole.ADMIN, AccountRole.COMPTABLE])
    @check_file_import()
    @api.doc(security="Bearer")
    def post(self):
        """
        Charge un fichier issue de l'excel France 2030
        Les lignes sont insérés de manière asynchrone
        """
        data = request.form
        user = ConnectedUser.from_current_token_identity()
        annee = int(data["annee"])

        file_france2030 = request.files["fichier"]

        task = import_france_2030(file_france2030, annee=annee, username=user.username)
        return jsonify(
            {
                "status": f"Fichier récupéré. Demande d`import des données FRANCE2030 en cours (taches asynchrone id = {task.id}"
            }
        )

    @api.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        """
        Retourne les lignes de financement France 2030
        """
        params = parser_get.parse_args()

        # TODO: implementer
        fake_data = {
            "Structure": "STRUCTURE FAKE",
            "Num\u00e9roDeSiretSiConnu": "22560001400016",
            "SubventionAccord\u00e9e": "516642.00",
            "Synth\u00e8se": "Pr\u00eats d'honneur - R\u00e9vision novembre 2021",
            "axe": "Coh\u00e9sion",
            "sous-axe": "Formation professionnelle",
            "dispositif": "Pr\u00eat d'honneur solidaire",
            "territoire": "D\u00e9partement du Morbihan entier",
        }

        return {"items": [fake_data], "pageInfo": Pagination(0, 1, 0).to_json(), "params": params}, HTTPStatus.OK


#############################################
# XXX: A terme, ce devra être des référentiels
#
parser_searchterm = reqparse.RequestParser()
parser_searchterm.add_argument("term", type=str, help="The search term")


@dataclasses.dataclass
class SousAxePlanRelancePayload:
    label: str
    axe: str


@dataclasses.dataclass
class StructurePayload:
    label: str
    siret: str


@dataclasses.dataclass
class TerritoirePayload:
    Commune: str
    CodeInsee: int


@api.route("/france-2030-axes")
class France2030Axes(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self) -> list[SousAxePlanRelancePayload]:
        # TODO: ne plus mocker
        sousaxe = SousAxePlanRelancePayload("tata", "toto")
        return [dataclasses.asdict(sousaxe)]  # type: ignore


@api.route("/france-2030-structures")
class France2030Structures(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.expect(parser_searchterm)
    @api.doc(security="Bearer")
    def get(self) -> list[StructurePayload]:
        # TODO: ne plus mocker

        _ = parser_get.parse_args()

        structure = StructurePayload("structure", "oui")
        return [dataclasses.asdict(structure)]  # type: ignore


@api.route("/france-2030-territoires")
class France2030Territoires(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.expect(parser_searchterm)
    @api.doc(security="Bearer")
    def get(self) -> list[StructurePayload]:
        # TODO: ne plus mocker

        _ = parser_get.parse_args()

        territoires = TerritoirePayload("structure", 1234)
        return [dataclasses.asdict(territoires)]  # type: ignore
