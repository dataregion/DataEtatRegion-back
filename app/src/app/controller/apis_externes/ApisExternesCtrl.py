from http import HTTPStatus
import logging

from flask import current_app, request
from flask_restx import Namespace, Resource, fields

from app.clients.demarche_simplifie import get_or_make_api_demarche_simplifie
from app.models.apis_externes.entreprise import InfoApiEntreprise
from app.models.apis_externes.error import Error as ApiError
from app.models.apis_externes.subvention import InfoApiSubvention
from app.services.demarches.tokens import TokenService
from app.servicesapp.api_externes import ApisExternesService
from app.servicesapp.authentication.connected_user import connected_user_from_current_token_identity

api = Namespace(
    name="External APIs",
    path="/",
    description="Controlleur qui construit les données via les APIs externes (api entreprise, data_subvention etc..)",
)

auth = current_app.extensions["auth"]

service = ApisExternesService()


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


@api.route("/info-subvention/<siret>")
class InfoSubventionCtrl(Resource):
    @auth("openid")
    @api.doc(security="Bearer")
    @api.response(200, "Success", model=InfoApiSubvention.schema_model(api))
    @_document_error_responses(api)
    def get(self, siret: str):
        logging.info("[API EXTERNES][CTRL] Info subventions")

        subvention = service.subvention(siret)
        json = InfoApiSubvention.ma_schema.dump(subvention)
        return json


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


@api.route("/info-entreprise/<siret>")
class InfoEntrepriseCtrl(Resource):
    @auth("openid")
    @api.doc(security="Bearer")
    @api.response(
        200,
        "Informations de l'API entreprise",
        model=InfoApiEntreprise.schema_model(api),
    )
    @_document_error_responses(api)
    def get(self, siret: str):
        logging.info("[API EXTERNES][CTRL] Info entreprise")

        entreprise = service.entreprise(siret)
        json = InfoApiEntreprise.ma_schema.dump(entreprise)
        return json


@api.route("/api-entreprise-batch/healthcheck")
class GetHealthcheckSiren(Resource):
    def get(self):
        """
        Effectue un GET pour vérifier la disponibilité de l'API Siren Batch
        """
        # Siret NumihFrance
        siret = "18310021300028"
        entreprise = service.entreprise(siret, use_batch=True)

        assert entreprise.donnees_etablissement.siret == siret
        return HTTPStatus.OK
