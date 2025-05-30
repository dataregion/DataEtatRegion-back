from app.controller import ApiDataEtat
from flask import Blueprint

from app.controller.administration.PreferenceUsersCtrl import api as prefApi
from app.controller.administration.AuditCtrl import api as auditApi
from app.controller.administration.ImportReferentielFinancial import api as importApi

api_administration = Blueprint("api_administration", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = ApiDataEtat(
    api_administration,
    doc="/doc",
    prefix="/api/v1",
    description="API d'administration, permettant de gérer les préférences, les utilisateurs " "et d'accéder aux audit",
    title="Gestion des paramétrages/utilisateurs, Audit",
    authorizations=authorizations,
)
api.add_namespace(auditApi)
api.add_namespace(prefApi)
api.add_namespace(importApi)
