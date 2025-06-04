from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import requests

from grist_plugins.settings import Settings

templates = Jinja2Templates(directory="templates")
router = APIRouter()
settings = Settings()

@router.get("/sync-referentiels", response_class=HTMLResponse)
async def to_superset_page(request: Request):
    return templates.TemplateResponse("sync_referentiels.html", {"request": request})


@router.post("/launch-sync")
def launch_sync():
  with requests.Session() as session:
    with session.post(f"{settings.url_sync_db}?token={settings.token_sync_db}") as response:
      return JSONResponse(status_code=response.status_code, content={ "message": "Référentiels synchronisés !"})
