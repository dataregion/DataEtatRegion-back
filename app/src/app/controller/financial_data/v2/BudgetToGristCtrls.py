from flask import current_app

from flask_restx import Namespace, Resource

from http import HTTPStatus

from gristcli.gristservices import UserDatabaseService

api_ns = Namespace(name="BudgetToGrist", path="/grist", description="Api d'accès aux données budgetaires.")
auth = current_app.extensions["auth"]


url_grist_db = current_app.config.get("SQLALCHEMY_GRIST")


@api_ns.route("/to-grist")
class BugdetToGrist(Resource):
    # @auth("openid")
    @api_ns.doc(security="OAuth2AuthorizationCodeBearer")
    def get(self):
        """Recupère les lignes de données budgetaires génériques"""

        userservice = UserDatabaseService(url_grist_db)
        user = userservice.get_user_by_id(10)

        return user, HTTPStatus.OK
