from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import requests

from grist_plugins.settings import Settings

templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)
router = APIRouter()
settings = Settings()


@router.get("/init-referentiels", response_class=HTMLResponse)
async def init_referentiels(request: Request, tableName: str):
    print(f"[DEBUG] tableName = {tableName}")
    return templates.TemplateResponse("init_referentiels.html", {"request": request, "tableName": tableName})

@router.get("/sync-referentiels", response_class=HTMLResponse)
async def sync_referentiels(request: Request, tableName: str):
    print(f"[DEBUG] tableName = {tableName}")
    return templates.TemplateResponse("sync_referentiels.html", {"request": request, "tableName": tableName})


@router.post("/init-sync")
def init_sync(docId: str, tableId: str, tableName: str):
    print(f"[DEBUG] method = POST")
    with requests.Session() as session:
        with session.post(
            f"{settings.url_init_sync_db}?docId={docId}&tableId={tableId}&tableName={tableName}&token={settings.token_sync_db}"
        ) as response:
            return JSONResponse(
                status_code=response.status_code,
                content={"message": "Demande d'initilisation de synchronisation envoyée"},
            )

@router.put("/launch-sync")
def launch_sync(docId: str, tableId: str, tableName: str):
    print(f"[DEBUG] method = PUT")
    with requests.Session() as session:
        with session.put(
            f"{settings.url_sync_db}?docId={docId}&tableId={tableId}&tableName={tableName}&token={settings.token_sync_db}"
        ) as response:
            return JSONResponse(
                status_code=response.status_code,
                content={"message": "Demande de synchronisation envoyée"},
            )
