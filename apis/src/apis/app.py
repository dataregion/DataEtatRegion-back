from http import HTTPStatus
from urllib.request import Request
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from models import init as init_persistence_module

init_persistence_module()

from models.entities import *  # type: ignore # noqa: E402 F403
from models.schemas import *  # type: ignore  # noqa: E402 F403
from models.value_objects import *  # type: ignore  # noqa: E402 F403

from apis.apps.budget.api import app as app_budget  # type: ignore  # noqa: E402
from apis.apps.referentiels.api import app as app_referentiels  # type: ignore  # noqa: E402
from apis.shared.models import APIError  # type: ignore  # noqa: E402


def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
        content=APIError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            success=False,
            message="Erreur de validation",
            error="ValidationError",
            detail=str(exc),
        ).model_dump(),
    )


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

    app.mount("/financial-data/api/v3", app_budget)
    app.mount("/referentiels/api/v3", app_referentiels)

    app.add_exception_handler(
        RequestValidationError, custom_validation_exception_handler
    )
    return app
