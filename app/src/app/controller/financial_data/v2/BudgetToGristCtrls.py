from app.servicesapp.authentication.connected_user import ConnectedUser
from app.services.grist.go_to_grist import GristCliService
from flask import current_app
from flask_restx import Namespace, Resource
from http import HTTPStatus


api_ns = Namespace(name="BudgetToGrist", path="/grist", description="Api pour communiquer avec Grist")
auth = current_app.extensions["auth"]


@api_ns.route("/to-grist")
class BugdetToGrist(Resource):
    @auth("openid")
    @api_ns.doc(security="OAuth2AuthorizationCodeBearer")
    def get(self):
        """Recupère les lignes de données budgetaires génériques"""
        user = ConnectedUser.from_current_token_identity()
        GristCliService.send_request_to_grist(user)
        return "", HTTPStatus.OK
