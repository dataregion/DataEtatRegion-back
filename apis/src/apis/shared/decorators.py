from functools import wraps
from fastapi.responses import JSONResponse
from http import HTTPStatus
from typing import Callable
import traceback


from apis.shared.models import APIError


def _to_json_response(content: APIError):
    status_code = content.code
    serialized = content.model_dump(mode="json")
    return JSONResponse(status_code=status_code, content=serialized)


def handle_exceptions(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            traceback.print_exc()
            error = APIError(code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(ve))
            return _to_json_response(error)
        except PermissionError as pe:
            traceback.print_exc()
            error = APIError(code=HTTPStatus.FORBIDDEN, detail=str(pe))
            return _to_json_response(error)
        except Exception as e:
            traceback.print_exc()
            error = APIError(code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))
            return _to_json_response(error)

    return wrapper
