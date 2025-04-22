from app.controller import ApiDataEtat
from flask import Blueprint

from app.controller.laureats_data.France2030Ctrl import api as api_france2030

api_laureats = Blueprint("laureats_data", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}
_description = (
    "API de gestion des données lauréats"
    "<br />"
    "<strong>C'est une API dediée à l'outil interne de consultation de lauréats. "
    "N'utilisez pas cette API pour intégrer nos données à votre système.</strong>"
)

_api = ApiDataEtat(
    api_laureats,
    doc="/doc",
    prefix="/api/v1",
    description=_description,
    title="API Laureats",
    authorizations=authorizations,
)

_api.add_namespace(api_france2030)
