import logging
from flask import Blueprint
from flask_restx import Api

logger = logging.getLogger(__name__)

from app.controller.ui_controller.UiController import api as uiApi

api_ui = Blueprint("api_ui", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(
  api_ui,
  prefix="/api/v1",
  doc="/doc", description="API pour fournir des données à l'UI", authorizations=authorizations)

api.add_namespace(uiApi)
