import logging
from fastapi import FastAPI

from apis.apps.apis_externes.models import ApiExterneError, CodeErreur
from api_entreprise.exceptions import ApiError as ApiEntrepriseError

from services.apis_externes.clients.data_subventions import CallError as DataSubventionsCallError
from services.apis_externes.clients.entreprise import LimitHitError

from apis.shared.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


def _log_exception(exc: Exception):
    logger.exception(f"Exception durant une requête API externes: {exc}")


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(InvalidTokenError)
    async def invalid_token_error(request: FastAPI, exc: InvalidTokenError):
        """Lorsqu'une erreur de token invalide est survenue"""
        _log_exception(exc)
        error = ApiExterneError(
            code=CodeErreur.CODE_INVALID_TOKEN,
            message="Token d'authentification invalide.",
            remote_errors=(),
        )
        return error.to_json_response(code_http=401)

    @app.exception_handler(LimitHitError)
    async def limit_hit_error(request: FastAPI, exc: LimitHitError):
        """Lorsqu'une limite d'usage API a été atteinte"""
        _log_exception(exc)
        error = ApiExterneError(
            code=CodeErreur.CODE_LIMIT_HIT,
            message=f"Limite d'utilisation API atteintes (réessayer dans {exc.delay} secondes)",
            remote_errors=(),
        )
        return error.to_json_response(code_http=429)

    @app.exception_handler(ApiEntrepriseError)
    async def api_entreprise_error(request: FastAPI, exc: ApiEntrepriseError):
        """Lorsqu'une erreur lors de l'appel à l'API entreprise est survenue"""
        _log_exception(exc)
        remote = exc.errors
        error = ApiExterneError(
            code=CodeErreur.CODE_CALL_FAILED,
            message="Erreur lors de l'appel à l'API Entreprise",
            remote_errors=remote,
        )
        return error.to_json_response()

    def _message_from_remote(error: DataSubventionsCallError) -> str:
        if (
            error.call_error_description.api_code == 0
        ):  # Code retourné pour une recherche sur une entité qui n'est pas une associaiton
            return "Echec lors de l'appel à l'API Data Subventions : L'entité n'est pas une associaiton."
        else:
            return "Erreur lors de l'appel à l'API Data Subventions"

    @app.exception_handler(DataSubventionsCallError)
    async def data_subventions_call_error(request: FastAPI, exc: DataSubventionsCallError):
        """Lorsqu'une erreur lors de l'appel à l'API Data Subventions est survenue"""
        _log_exception(exc)
        remote = exc.call_error_description
        message = _message_from_remote(exc)
        error = ApiExterneError(
            code=CodeErreur.CODE_CALL_FAILED,
            message=message,
            remote_errors=[remote],
        )
        return error.to_json_response()

    @app.exception_handler(Exception)
    async def all(request: FastAPI, exc: Exception):
        """Lorsqu'une erreur inconnue est survenue"""
        _log_exception(exc)
        error = ApiExterneError(code=CodeErreur.CODE_UNKNOWN, message=str(exc), remote_errors=())
        return error.to_json_response()
