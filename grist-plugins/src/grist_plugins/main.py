from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from grist_plugins.routes import to_superset, sync_referentiels

app = FastAPI()

static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

templates = Jinja2Templates(directory="templates")

# Inclusion des routes
app.include_router(to_superset.router)
app.include_router(sync_referentiels.router)
