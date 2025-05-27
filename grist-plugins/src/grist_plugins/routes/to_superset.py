from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/to-superset", response_class=HTMLResponse)
async def to_superset_page(request: Request):
    return templates.TemplateResponse("to_superset.html", {"request": request})