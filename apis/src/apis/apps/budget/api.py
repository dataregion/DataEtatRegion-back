from fastapi import FastAPI

from apis.apps.budget.routers.healthcheck import router as router_healthcheck
from apis.apps.budget.routers.lignes_financieres import (
    router as router_lignes_financieres,
)
from apis.apps.budget.routers.details_paiement import router as router_details_paiement
from apis.apps.budget.routers.colonnes import router as router_colonnes

from apis.apps.budget.routers.import_chorus import tus_router


app = FastAPI(
    title="API V3 - Data Etat - Budget",
    description="""
Api de d'accès aux données financières de l'état
<b>C'est une API dediée à l'outil interne de consultation budget. N'utilisez pas cette API pour intégrer nos données à votre système.</b>
    """,
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
)

app.include_router(router_healthcheck, prefix="/healthcheck", tags=["Healthcheck"])
app.include_router(router_colonnes, prefix="/colonnes", tags=["Liste des colonnes"])
app.include_router(router_lignes_financieres, prefix="/lignes", tags=["Lignes financieres"])
app.include_router(router_details_paiement, prefix="/lignes", tags=["Détails paiement"])

app.include_router(tus_router)
