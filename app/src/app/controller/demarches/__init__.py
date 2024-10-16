import logging
from flask import Blueprint
from flask_restx import Api

from app.controller.demarches.DemarchesCtrl import api as demarchesApi

logger = logging.getLogger(__name__)

api_demarches = Blueprint("api_demarches", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

_description = (
    "API de gestion des données sauvegardées de l'API Démarches simplifiées"
    "<br />"
    "<strong>C'est une API dediée à la sauvegarde et consultation des données de Démarches Simplifiées.</strong>"
)

api = Api(api_demarches, doc="/doc", description=_description, authorizations=authorizations)

api.add_namespace(demarchesApi)
