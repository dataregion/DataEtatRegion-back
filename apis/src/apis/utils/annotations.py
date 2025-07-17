from functools import wraps
from http import HTTPStatus
from typing import Callable

from apis.utils.models import APIError


def handle_exceptions(func: Callable):
  @wraps(func)
  async def wrapper(*args, **kwargs):
    try:
      return await func(*args, **kwargs)
    except ValueError as ve:
      return APIError(
        code=HTTPStatus.BAD_REQUEST,
        detail=str(ve)
      ).to_json_response()
    except PermissionError as pe:
      return APIError(
        code=HTTPStatus.FORBIDDEN,
        detail=str(pe)
      ).to_json_response()
    except Exception as e:
      return APIError(
        code=HTTPStatus.INTERNAL_SERVER_ERROR,
        detail=str(e)
      ).to_json_response()

  return wrapper

