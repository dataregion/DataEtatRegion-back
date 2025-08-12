from flask import current_app, jsonify
from app.servicesapp.authentication.connected_user import connected_user_from_current_token_identity
from flask_restx import Namespace, Resource

api = Namespace(
    name="Ressource", path="/", description="Api d'accès aux ressources disponibles en fonction du code region."
)
auth = current_app.extensions["auth"]


@api.route("/liste")
class RessourceCtrl(Resource):
    @auth("openid")
    @api.doc(security="Bearer")
    def get(self):
        """Recupère les ressources disponibles en fonction du code region."""
        user = connected_user_from_current_token_identity()
        ressources_config = current_app.config.get("ressources", {})
        ressources = ressources_config.get(user.current_region, ressources_config["default"])

        return jsonify(ressources)
