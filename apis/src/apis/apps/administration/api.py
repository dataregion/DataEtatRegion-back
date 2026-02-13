"""API FastAPI pour l'administration - v3."""

from fastapi import FastAPI
from apis.apps.administration.routers import preferences

app = FastAPI(
    title="API V3 - Administration",
    description="""
API de gestion des fonctionnalités d'administration :
- Préférences utilisateurs (création, modification, suppression, partage)
- Recherche d'utilisateurs Keycloak
    """,
    openapi_url="/admin/openapi.json",
    docs_url="/docs",
    version="3.0.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
)

app.include_router(preferences.router)
