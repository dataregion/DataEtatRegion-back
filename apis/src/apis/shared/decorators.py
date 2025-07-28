from functools import wraps
from http import HTTPStatus
from typing import Callable
import traceback

from fastapi import Request

from apis.shared.models import APIError


from requests import RequestException

from apis.security.keycloak_token_validator import ConnectedUser
from apis.shared.enums import AccountRole


def handle_exceptions(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            traceback.print_exc()
            return APIError(
                code=HTTPStatus.BAD_REQUEST,
                detail=str(ve)
            ).to_json_response()
        except PermissionError as pe:
            traceback.print_exc()
            return APIError(
                code=HTTPStatus.FORBIDDEN,
                detail=str(pe)
            ).to_json_response()
        except Exception as e:
            traceback.print_exc()
            return APIError(
                code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=str(e)
            ).to_json_response()

    return wrapper


def check_permission(permissions):
    """Decorator that checks if the user has the specified permission.

    If the user does not have the permission, the decorated function returns an HTTP 403 error response.

    Args:
        permissions (Union[str, List[str]]): The permission required to execute the decorated function. It can be a single string or a list of strings.

    Returns:
        inner_wrapper (function): The decorated function, which checks if the user has the specified permission before executing it.
    """

    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            user = ConnectedUser.from_current_token_identity()

            if isinstance(permissions, AccountRole):
                permissions_to_check = [permissions]
            elif isinstance(permissions, list):
                permissions_to_check = permissions
            else:
                raise TypeError("permissions should be an AccountRole or a list of AccountRole")

            if user.roles is None:
                return PermissionError("Vous n'avez pas les droits")

            for perm in permissions_to_check:
                if perm in user.roles:
                    return func(*args, **kwargs)  # the user has the required permission

            return PermissionError("Vous n'avez pas les droits")

        return inner_wrapper

    return wrapper


def retry_on_exception(max_retry):
    """
    A decorator to retry a function call in case of exceptions.
    :param max_retry: Maximum number of retries.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retry:
                try:
                    return func(*args, **kwargs)
                except RequestException as e:
                    retry_count += 1
                    if retry_count == max_retry:
                        raise e

        return wrapper

    return decorator


def authM2M(expected_token):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get the Request object
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise RuntimeError("Request object not found in arguments")

            token = request.query_params.get("token")
            if token != expected_token:
                raise PermissionError("Unauthorized: Invalid token")
            return func(*args, **kwargs)

        return wrapper

    return decorator
