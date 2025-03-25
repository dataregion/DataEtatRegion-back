import logging
from app.controller import ApiDataEtat
from flask import Blueprint

from app.controller.apis_externes.ApisExternesCtrl import api as externalApi

logger = logging.getLogger(__name__)

api_apis_externes = Blueprint("api_apis_externes", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = ApiDataEtat(
    api_apis_externes, doc="/doc", description="API proxy de data subventions", authorizations=authorizations
)

from . import errorhandlers  # noqa: E402, F401

api.add_namespace(externalApi)
