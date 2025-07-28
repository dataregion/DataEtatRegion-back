from http.client import HTTPException
from urllib.request import Request
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine


from models.entities import *  # type: ignore # noqa: F403
from models.schemas import *  # type: ignore  # noqa: F403
from models.value_objects import *  # type: ignore  # noqa: F403

from apis.apps.administration.api import app as app_administration
from apis.apps.budget.api import app as app_budget
from apis.apps.referentiels.api import app as app_referentiels


app = FastAPI(
    title="API V3 - Data Etat",
    docs_url="/docs",
    version="3.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.mount("/v3/administration", app_administration)
app.mount("/v3/budget", app_budget)
app.mount("/v3/referentiels", app_referentiels)
