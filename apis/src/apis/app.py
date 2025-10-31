import asyncio
import logging
from apis.clients import RedisClientHolder
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.cors import CORSMiddleware
from models import init as init_persistence_module

from apis.exception_handlers import setup_exception_handlers
from apis.security.keycloak_token_validator import KeycloakTokenValidator

from models.value_objects.redis_events import MAT_VIEWS_REFRESHED_EVENT_CHANNEL
from apis.services.pubsub import listens

init_persistence_module()

from models.entities import *  # type: ignore # noqa: E402 F403
from models.schemas import *  # type: ignore  # noqa: E402 F403
from models.value_objects import *  # type: ignore  # noqa: E402 F403

from apis.apps.apis_externes.api import app as app_apis_externe  # type: ignore  # noqa: E402
from apis.apps.budget.api import app as app_budget  # type: ignore  # noqa: E402
from apis.apps.referentiels.api import app as app_referentiels  # type: ignore  # noqa: E402


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.keycloak_token_validator = KeycloakTokenValidator.get_application_instance()
    app.state.redis = RedisClientHolder.get_application_instance()

    channels = [MAT_VIEWS_REFRESHED_EVENT_CHANNEL]
    app.state.listener_task = asyncio.create_task(listens(channels))

    yield

    app.state.listener_task.cancel()
    try:
        await app.state.listener_task
    except asyncio.CancelledError as e:
        logger.error("Listener task cancelled", exc_info=e)
    await app.state.redis.close()


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
        lifespan=lifespan,
    )

    _ = Instrumentator().instrument(app).expose(app)

    # XXX pas d'exception handler général pour les api externes
    # setup_exception_handlers(app_apis_externe)
    setup_exception_handlers(app_budget)
    setup_exception_handlers(app_referentiels)

    app.mount("/apis-externes/v3", app_apis_externe)
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
