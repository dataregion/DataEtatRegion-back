from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import httpx

from grist_plugins.settings import settings
from grist_plugins.routes import to_superset, sync_referentiels
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if settings.dev_mode:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger().setLevel(logging.DEBUG)

app = FastAPI()


# Gestionnaire d'exceptions global pour les erreurs de connexion
@app.exception_handler(httpx.ConnectError)
async def handle_connect_error(request: Request, exc: httpx.ConnectError):
    logging.error(f"Erreur de connexion à l'API distante: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "message": "Le service de destination est temporairement indisponible. Veuillez réessayer ultérieurement.",
        },
    )


@app.exception_handler(httpx.TimeoutException)
async def handle_timeout_error(request: Request, exc: httpx.TimeoutException):
    logging.error(f"Timeout lors de la connexion à l'API distante: {exc}")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "success": False,
            "message": "Le service de destination met trop de temps à répondre. Veuillez réessayer.",
        },
    )


@app.exception_handler(httpx.HTTPError)
async def handle_http_error(request: Request, exc: httpx.HTTPError):
    logging.error(f"Erreur HTTP lors de la communication avec l'API distante: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "success": False,
            "message": "Une erreur s'est produite lors de la communication avec le service. Veuillez contacter l'administrateur.",
        },
    )


static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

templates = Jinja2Templates(directory="templates")

# Inclusion des routes
app.include_router(to_superset.router)
app.include_router(sync_referentiels.router)
