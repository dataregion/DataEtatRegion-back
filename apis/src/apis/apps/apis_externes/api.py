from fastapi import FastAPI

from apis.apps.apis_externes.routers.healthcheck import router as router_healthcheck
from apis.apps.apis_externes.routers.entreprise import router as router_entreprise
from apis.apps.apis_externes.routers.data_subventions import router as router_data_subventions

from .errorhandlers import setup_exception_handlers

app = FastAPI(
    title="API V3 - Data Etat - API externes",
    openapi_url="/admin/openapi.json",
    description="""
API d'accès aux données externes au système Data Etat.
<b>C'est une API dediée au fonctionnement interne Data Etat. Merci de ne pas utiliser cette API pour vos intégrations M2M.</b>
    """,
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.include_router(router_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])
app.include_router(router_entreprise, prefix="/info-entreprise", tags=["Entreprise"])
app.include_router(router_data_subventions, prefix="/info-subvention", tags=["Subvention"])

setup_exception_handlers(app)
