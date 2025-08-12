from functools import wraps
from http import HTTPStatus
from typing import Callable
import traceback


from apis.shared.models import APIError


def handle_exceptions(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            traceback.print_exc()
            return APIError(code=HTTPStatus.BAD_REQUEST, detail=str(ve))
        except PermissionError as pe:
            traceback.print_exc()
            return APIError(code=HTTPStatus.FORBIDDEN, detail=str(pe))
        except Exception as e:
            traceback.print_exc()
            return APIError(code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

    return wrapper
