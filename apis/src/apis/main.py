from http.client import HTTPException
from urllib.request import Request
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine


from models.entities import *  # type: ignore # noqa: F403
from models.schemas import *  # type: ignore  # noqa: F403
from models.value_objects import *  # type: ignore  # noqa: F403

from apis.budget.api import app as app_budget
from apis.referentiels.api import app as app_referentiels

from models import Base


"""Create a FastAPI application."""
app = FastAPI(
    title="API V3 - Data Etat",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

# Mount sub-apps
app.mount("/v3/budget", app_budget)
app.mount("/v3/referentiels", app_referentiels)
