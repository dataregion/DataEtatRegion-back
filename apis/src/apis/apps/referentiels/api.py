from fastapi import FastAPI

from apis.apps.referentiels.routers.healthcheck import router as router_healthcheck
from apis.apps.referentiels.routers import all_referentiel_routers


app = FastAPI(
    title="API V3 - Data Etat - Référentiels",
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.include_router(router_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])

for router in all_referentiel_routers:
    app.include_router(router)
