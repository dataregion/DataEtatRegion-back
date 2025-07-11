from functools import wraps

from flask import request
from requests import RequestException

from app.controller import ErrorController
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication import ConnectedUser


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
                return _unauthorized_response()

            for perm in permissions_to_check:
                if perm in user.roles:
                    return func(*args, **kwargs)  # the user has the required permission

            return _unauthorized_response()

        return inner_wrapper

    return wrapper


def _unauthorized_response():
    response_body = ErrorController("Vous n`avez pas les droits").to_json()
    return response_body, 403, {"WWW-Authenticate": "Bearer"}


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
            token = request.args.get("token")
            if token != expected_token:
                raise PermissionError("Unauthorized: Invalid token")
            return func(*args, **kwargs)

        return wrapper

    return decorator
