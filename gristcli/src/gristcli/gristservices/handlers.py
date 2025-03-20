import functools

from requests import HTTPError, Response

from gristcli.gristservices.errors import ApiGristError, CallErrorDescription


def _handle_httperror(response: Response):
    code = response.status_code

    description = CallErrorDescription(code, response.text)
    raise ApiGristError(description)


def _handle_error_grist_api(f):
    """Décorateur pour gérer une erreur de l'API Grist"""

    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPError as e:
            response: Response = e.response
            _handle_httperror(response)

    return inner
