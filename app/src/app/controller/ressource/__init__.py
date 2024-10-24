import logging
from flask import Blueprint
from flask_restx import Api

from app.controller.ressource.RessourceCtrl import api as ressourceApi

logger = logging.getLogger(__name__)

api_ressource = Blueprint("api_ressource", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

_description = "Api d'accès aux ressources disponibles en fonction du code region."

api = Api(api_ressource, doc="/doc", description=_description, authorizations=authorizations)

api.add_namespace(ressourceApi)
