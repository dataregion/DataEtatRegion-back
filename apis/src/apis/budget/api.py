from fastapi import FastAPI

from apis.budget.routers.healthcheck import router as router_healthcheck
from apis.budget.routers.lignes_financieres import router as router_lignes_financieres
from apis.budget.routers.colonnes import router as router_colonnes


app = FastAPI(
    title="API V3 - Data Etat - Budget",
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.include_router(router_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])
app.include_router(router_colonnes, prefix="/colonnes", tags=["Liste des colonnes"])
app.include_router(router_lignes_financieres, prefix="/lignes", tags=["Lignes financières"])
