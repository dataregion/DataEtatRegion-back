from fastapi import FastAPI

from apis.apps.administration.routers.preferences import router as router_preferences
from apis.apps.administration.routers.users import router as router_users


app = FastAPI(
    title="API V3 - Data Etat - Administration",
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.include_router(router_preferences, prefix="/preferences", tags=["Préférences"])
app.include_router(router_users, prefix="/users", tags=["Utilisateurs"])
