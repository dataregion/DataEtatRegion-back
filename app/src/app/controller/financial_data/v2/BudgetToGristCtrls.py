from app.controller.utils.Error import ErrorController
from app.exceptions.exceptions import BadRequestDataRegateNum
from app.services.grist.__init_ import ParsingColumnsError
from app.servicesapp.authentication.connected_user import ConnectedUser
from app.services.grist.go_to_grist import GristCliService
from flask import current_app, request
from flask_restx import Namespace, Resource, fields
from http import HTTPStatus

from gristcli.gristservices.errors import ApiGristError


api_ns = Namespace(name="BudgetToGrist", path="/grist", description="Api pour communiquer avec Grist")
auth = current_app.extensions["auth"]


@api_ns.errorhandler(ApiGristError)
def handle_exception_grist(e: ApiGristError):
    return ErrorController(e.message).to_json(), e.call_error_description.code


@api_ns.errorhandler(ParsingColumnsError)
def handle_exception_parsing_columns(e: ParsingColumnsError):
    return ErrorController(e.message).to_json(), HTTPStatus.BAD_REQUEST


data_model = api_ns.model(
    "GristDataModel",
    {
        "data": fields.List(
            fields.Raw(),
            required=True,
            example=[
                {"Année engagement": 2024, "ej": "11111", "montant": 100, "Programme": "programme1"},
                {"Année engagement": 2024, "ej": "2222", "montant": 100, "Programme": "programme2"},
                {"Année engagement": 2024, "ej": "3333", "montant": 100, "Programme": "programme3"},
            ],
            description="Liste d'objets sous forme clé valeur. La clé correspond à la colonne de grist.",
        ),
    },
)


@api_ns.route("")
class BugdetToGrist(Resource):
    @auth("openid")
    @api_ns.expect(data_model)
    @api_ns.doc(security="OAuth2AuthorizationCodeBearer")
    @api_ns.response(201, "Success")
    @api_ns.response(400, "Bad request")
    @api_ns.response(403, "Forbidden")
    def post(self):
        """Récupère les données passé dans le body et les injectes dans le grist"""

        payload = request.json  # Récupère le JSON envoyé
        if not isinstance(payload, dict) or "data" not in payload:
            raise BadRequestDataRegateNum("Donnée non valide")

        data_list = payload.get("data", [])

        if not isinstance(payload, dict) or "data" not in payload:
            raise BadRequestDataRegateNum("La clé 'data' doit contenir une liste non vide.")

        user = ConnectedUser.from_current_token_identity()
        GristCliService.send_request_to_grist(user, data_list)

        return HTTPStatus.CREATED
