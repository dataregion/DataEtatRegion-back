from fastapi import FastAPI
from apis.apps.grist_to_superset.routers.grist_to_superset import router as grist_to_superset


app = FastAPI(
    title="API - Grist to Superset",
    openapi_url="/admin/openapi.json",
    description="""
API permettant de créer une base de donnée pour un utilisateur dans un schema particulier et construit le dataSource dans superset.
<b>C'est une API dediée au fonctionnement interne Data Etat Grist. Merci de ne pas utiliser cette API pour vos intégrations M2M.</b>
    """,
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.include_router(grist_to_superset, prefix="", tags=["Grist to Superset"])
