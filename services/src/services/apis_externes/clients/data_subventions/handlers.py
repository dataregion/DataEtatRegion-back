import functools

from requests import HTTPError, Response

from .errors import CallError, CallErrorDescription


def _handle_httperror(response: Response):
    code = response.status_code
    
    try:
        json = response.json()
        api_code = json.get("code", code)
        message = json.get("message", None)
    except Exception: # XXX: normal, c'est juste la gestion d'erreur
        pass

    description = CallErrorDescription(code, api_code, message) # type: ignore
    raise CallError(description)


def _handle_response_in_error(f):
    """Décorateur pour gérer une erreur de l'API data subvention"""

    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPError as e:
            response: Response = e.response
            _handle_httperror(response)

    return inner
