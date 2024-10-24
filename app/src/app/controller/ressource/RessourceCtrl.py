from flask import current_app, jsonify
from flask_pyoidc import OIDCAuthentication
from app.servicesapp.authentication.connected_user import ConnectedUser
from flask_restx import Namespace, Resource

api = Namespace(
    name="Ressource", path="/", description="Api d'accès aux ressources disponibles en fonction du code region."
)
auth: OIDCAuthentication = current_app.extensions["auth"]


@api.route("/liste")
class RessourceCtrl(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        """Recupère les ressources disponibles en fonction du code region."""
        user = ConnectedUser.from_current_token_identity()
        ressources_config = current_app.config.get("ressources", {})
        ressources = ressources_config.get(user.current_region, ressources_config["default"])

        return jsonify(ressources)
