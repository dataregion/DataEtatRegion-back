from fastapi import FastAPI

from apis.referentiels.routers.healthcheck import router as router_healthcheck


app = FastAPI(
    title="API V3 - Data Etat - Référentiels",
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)


app.include_router(router_healthcheck, tags=["Healthcheck"])
