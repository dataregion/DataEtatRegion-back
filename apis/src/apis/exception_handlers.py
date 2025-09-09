from http import HTTPStatus
import fastapi
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from apis.shared.exceptions import (
    _APIException,
    BadRequestError,
    InvalidTokenError,
    ServerError,
)
from apis.shared.models import APIError


def _to_json_response(content: APIError):
    status_code = content.code
    serialized = content.model_dump(mode="json")
    return JSONResponse(status_code=status_code, content=serialized)


def error_responses() -> dict:
    """responses d'erreurs qui correspondant à la gestion d'exceptions"""
    _400_example = APIError(code=400)
    _401_example = APIError(code=401)
    _422_example = APIError(code=422)
    _500_example = APIError(code=500)

    return {
        400: {
            "model": APIError,
            "content": {"application/json": {"example": _400_example}},
        },
        401: {
            "model": APIError,
            "content": {"application/json": {"example": _401_example}},
        },
        422: {
            "model": APIError,
            "content": {"application/json": {"example": _422_example}},
        },
        500: {
            "model": APIError,
            "content": {"application/json": {"example": _500_example}},
        },
    }


def setup_exception_handlers(app: fastapi.applications.FastAPI):

    async def _api_exc_handler(request: fastapi.Request, exc: _APIException):
        code = exc.code
        message = exc.api_message

        error = APIError(
            code=code,
            message=message,
        )
        return _to_json_response(error)

    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request: fastapi.Request, exc: BadRequestError):
        return await _api_exc_handler(request, exc)

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: fastapi.Request, exc: InvalidTokenError):
        return await _api_exc_handler(request, exc)

    @app.exception_handler(ServerError)
    async def server_error_handler(request: fastapi.Request, exc: ServerError):
        return await _api_exc_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(
        _: fastapi.Request, exc: RequestValidationError
    ):
        error = APIError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY.value,
            success=False,
            message="Erreur de validation",
            detail=str(exc),
        )
        return _to_json_response(error)

    @app.exception_handler(Exception)
    async def all_validation_exc_handler(_: fastapi.Request, exc: Exception):
        error = APIError(
            code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            message="Une erreur interne est survenue.",
        )
        return _to_json_response(error)
