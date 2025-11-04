from flask import current_app, request
from flask_restx import Namespace, Resource, fields

from app.clients.demarche_simplifie import get_or_make_api_demarche_simplifie
from app.models.apis_externes.error import Error as ApiError
from app.services.demarches.tokens import TokenService
from app.servicesapp.authentication.connected_user import connected_user_from_current_token_identity

api = Namespace(
    name="External APIs",
    path="/",
    description="Controlleur qui construit les données via les APIs externes (api entreprise, data_subvention etc..)",
)

auth = current_app.extensions["auth"]


def _document_error_responses(api: Namespace):
    """Décorateur qui décrit les différentes réponses en erreur possibles"""

    def decorator(f):
        @api.response(
            500,
            "Lors d'une erreur inconnue",
            model=ApiError.schema_model(api),
        )
        @api.response(
            429,
            "Lors d'une erreur inconnue",
            model=ApiError.schema_model(api),
        )
        def inner(*args, **kwargs):
            return f(*args, **kwargs)

        return inner

    return decorator


parser_ds = api.model(
    "query",
    {"operationName": fields.String(required=True), "query": fields.String, "variables": fields.Raw(required=False)},
)


@api.route("/demarche-simplifie")
class DemarcheSimplifie(Resource):
    @auth("openid")
    @api.doc(security="Bearer")
    @api.expect(parser_ds)
    @_document_error_responses(api)
    def post(self):
        user = connected_user_from_current_token_identity()
        token_id = int(request.args["tokenId"])
        token = TokenService.find_by_uuid_utilisateur_and_token_id(user.sub, token_id).token
        return get_or_make_api_demarche_simplifie(token).do_post(request.get_data()).get("data")
