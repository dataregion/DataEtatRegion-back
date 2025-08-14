from fastapi import FastAPI
from models import init as init_persistence_module

from apis.exception_handlers import setup_exception_handlers

init_persistence_module()

from models.entities import *  # type: ignore # noqa: E402 F403
from models.schemas import *  # type: ignore  # noqa: E402 F403
from models.value_objects import *  # type: ignore  # noqa: E402 F403

from apis.apps.budget.api import app as app_budget  # type: ignore  # noqa: E402
from apis.apps.referentiels.api import app as app_referentiels  # type: ignore  # noqa: E402


def create_app():
    app = FastAPI(
        title="API V3 - Data Etat",
        docs_url="/docs",
        version="3.0",
        swagger_ui_parameters={
            "syntaxHighlight.theme": "obsidian",
            "docExpansion": "none",
        },
        separate_input_output_schemas=False,
    )

    setup_exception_handlers(app_budget)
    setup_exception_handlers(app_referentiels)

    app.mount("/financial-data/api/v3", app_budget)
    app.mount("/referentiels/api/v3", app_referentiels)

    return app
