from http import HTTPStatus
import json
import logging
from fastapi import FastAPI
import pandas
from apis.apps.grist_to_superset.exceptions.import_data_exceptions import (
    DataInsertException,
    DataInsertIndexException,
    UserNotFoundException,
)
from apis.shared.exceptions import BadRequestError
from pydantic_core import ValidationError

logger = logging.getLogger(__name__)


def _log_exception(exc: Exception):
    logger.exception(f"Exception durant l'import des données Grist vers la base: {exc}")


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(pandas.errors.EmptyDataError)
    async def empty_csv_error(request: FastAPI, exc: pandas.errors.EmptyDataError):
        """Lorsqu'une erreur de token invalide est survenue"""
        _log_exception(exc)
        raise BadRequestError(code=HTTPStatus.BAD_REQUEST, api_message="Le fichier CSV est vide")

    @app.exception_handler(pandas.errors.ParserError)
    async def parser_csv_error(request: FastAPI, exc: pandas.errors.ParserError):
        _log_exception(exc)
        raise BadRequestError(code=HTTPStatus.BAD_REQUEST, api_message=f"Erreur lors de la lecture du CSV: {str(exc)}")

    @app.exception_handler(json.JSONDecodeError)
    async def json_error(request: FastAPI, e: json.JSONDecodeError):
        _log_exception(e)
        raise BadRequestError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY, api_message=f"Format JSON invalide pour les colonnes: {str(e)}"
        )

    @app.exception_handler(DataInsertException)
    @app.exception_handler(DataInsertIndexException)
    async def data_insert_error(request: FastAPI, e: DataInsertException):
        raise BadRequestError(
            code=HTTPStatus.INTERNAL_SERVER_ERROR,
            api_message=str(e),
        )

    @app.exception_handler(UserNotFoundException)
    async def user_not_exist_superset(request: FastAPI, e: DataInsertException):
        raise BadRequestError(
            code=HTTPStatus.BAD_REQUEST,
            api_message="L'utilisateur n'est pas présent dans Superset",
        )

    @app.exception_handler(ValidationError)
    async def validation_error(request: FastAPI, e: ValidationError):
        _log_exception(e)
        raise BadRequestError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY, api_message=f"Erreur de validation du schéma des colonnes: {str(e)}"
        )
