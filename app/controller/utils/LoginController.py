import json
import logging

from flask import request
from flask_restx import Namespace, fields, Resource, abort
from flask_restx._http import HTTPStatus
from keycloak import KeycloakAuthenticationError

from app.clients.keycloack.factory import make_or_get_keycloack_openid, KeycloakConfigurationException
from app.controller import ErrorController

api = Namespace(name="Auth Controller", path="/auth", description="API de récupération de jeton d'authentification")


login_fields = api.model("Login", {"email": fields.String(required=True), "password": fields.String(required=True)})


@api.errorhandler(KeycloakConfigurationException)
def handler_bad_configuration(e):
    return ErrorController(e.message).to_json(), HTTPStatus.INTERNAL_SERVER_ERROR


@api.errorhandler(KeycloakAuthenticationError)
def handler_forbidden(e):
    return ErrorController(e.__str__()).to_json(), HTTPStatus.FORBIDDEN


@api.route("/login")
class Login(Resource):
    @api.response(200, "Success")
    @api.expect(login_fields, validate=True)
    def post(self):
        body = request.data

        param = json.loads(body)
        logging.info(f"[LOGIN] Login user {param['email']}")
        client = make_or_get_keycloack_openid()
        token = client.token(param["email"], param["password"])
        return f"{token['token_type']} {token['access_token']}", HTTPStatus.OK
