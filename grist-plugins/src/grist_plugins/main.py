from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

# Templating
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Hello Grist"})
