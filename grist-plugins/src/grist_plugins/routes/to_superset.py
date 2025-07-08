from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)
router = APIRouter()


@router.get("/to-superset", response_class=HTMLResponse)
async def to_superset_page(request: Request):
    return templates.TemplateResponse("to_superset.html", {"request": request})
