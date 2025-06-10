from fastapi.responses import JSONResponse
import requests

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .routes import to_superset, sync_referentiels

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Inclusion des routes
app.include_router(to_superset.router)
app.include_router(sync_referentiels.router)
