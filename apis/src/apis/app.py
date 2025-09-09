from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.cors import CORSMiddleware
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

    _ = Instrumentator().instrument(app).expose(app)

    setup_exception_handlers(app_budget)
    setup_exception_handlers(app_referentiels)

    app.mount("/financial-data/api/v3", app_budget)
    app.mount("/referentiels/api/v3", app_referentiels)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
