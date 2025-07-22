from fastapi import FastAPI

from apis.budget.routers.healthcheck import router as router_healthcheck
from apis.budget.routers.lignes_financieres import router as router_lignes_financieres
from apis.budget.routers.utils import router as router_utils


app = FastAPI(
    title="API V3 - Data Etat - Budget",
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)


app.include_router(router_healthcheck, tags=["Healthcheck"])
app.include_router(router_utils, tags=["Utilitaires"])
app.include_router(router_lignes_financieres, tags=["Lignes financières"])
