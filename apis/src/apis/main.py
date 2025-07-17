
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware, db

from models.entities import *  # type: ignore # noqa: F403
from models.schemas import *  # type: ignore  # noqa: F403
from models.value_objects import *  # type: ignore  # noqa: F403

from apis.budget.routers import router as budget_router
from apis.referentiels.routers import router as referentiels_router

from models import Base
print("Registered tables:", list(Base.metadata.tables.keys()))

"""Create a FastAPI application."""
app = FastAPI(
    title="API du portail de services",
    docs_url="/docs",
    version="1.0",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian", "docExpansion": "none"},
    separate_input_output_schemas=False,
)

app.add_middleware(
    DBSessionMiddleware,
    db_url="postgresql+psycopg://postgres:passwd@localhost:15432/DB",
    engine_args={
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    },
)


app.include_router(budget_router, prefix="/v3/budget", tags=["Budget"])
app.include_router(referentiels_router, prefix="/v3/referentiels", tags=["Référentiels"])
