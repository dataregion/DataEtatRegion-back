from fastapi import FastAPI

from apis.apps.qpv.routers.healthcheck import router as router_healthcheck
from apis.apps.qpv.routers.lignes_financieres import (
    router as router_lignes_financieres,
)
from apis.apps.qpv.routers.dashboards import (
    router as router_dashboards,
)
from apis.apps.qpv.routers.colonnes import router as router_colonnes


app = FastAPI(
    title="API V3 - Data Etat - Data QPV",
    description="""
Api de d'accès aux données financières des quartiers prioritaires de la ville
<b>C'est une API dediée à l'outil interne de consultation Data QPV. N'utilisez pas cette API pour intégrer nos données à votre système.</b>
    """,
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
)

app.include_router(router_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])
app.include_router(router_colonnes, prefix="/colonnes", tags=["Liste des colonnes"])
app.include_router(router_lignes_financieres, prefix="/lignes", tags=["Lignes financieres"])
app.include_router(router_dashboards, prefix="/dashboards", tags=["Dashboards"])
