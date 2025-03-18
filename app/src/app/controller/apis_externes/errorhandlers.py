import dataclasses

from app.clients.data_subventions import CallError as ApiSubventionCallError
from app.clients.entreprise import ApiError as ApiEntrepriseError, LimitHitError
from app.models.apis_externes.error import (
    Error as ApiError,
    CODE_UNKNOWN,
    CODE_CALL_FAILED,
    CODE_LIMIT_HIT,
    CODE_INVALID_TOKEN,
    CODE_DEMARCHE_NOT_FOUND,
    CODE_UNAUTHORIZED_ON_DEMARCHE,
)
from . import api
from . import logger
from ...clients.demarche_simplifie.errors import InvalidTokenError, UnauthorizedOnDemarche, DemarcheNotFound


#
# Exceptions de l'API subvention
#
@api.errorhandler(ApiSubventionCallError)
@api.response(500, "Internal Server Error", model=ApiError.schema_model(api))
def handle_api_subvention_call_error(error: ApiSubventionCallError):
    """Lorsqu'une erreur lors d'un appel à l'API subvention est survenue"""

    logger.error("[API EXTERNES][CTRL] " "Une erreur lors de l'appel à l'API subvention est survenue")

    desc = error.call_error_description
    message = (
        desc.description
        if desc.description is not None
        else "Une erreur lors de l'appel à l'API subvention est survenue"
    )
    err = ApiError(code=CODE_CALL_FAILED, message=message, remote_errors=[desc])
    dict = dataclasses.asdict(err)
    return dict


#
# Exceptions de l'api entreprise
#
@api.errorhandler(LimitHitError)
@api.response(429, "Limite d'usage API atteint", model=ApiError.schema_model(api))
def handle_limit_hit(error: LimitHitError):
    """Lorsqu'une limite d'usage API a été atteint"""

    msg = f"Limite d'utilisation API atteintes (réessayer dans {error.delay} secondes)"
    logger.error(f"[API EXTERNES][CTRL] {msg}")

    err = ApiError(
        code=CODE_LIMIT_HIT,
        message=f"{msg}",
    )
    dict = dataclasses.asdict(err)
    return dict


@api.errorhandler(ApiEntrepriseError)
@api.response(500, "Internal Server Error", model=ApiError.schema_model(api))
def handle_api_entreprise_error(error: ApiEntrepriseError):
    """Lorsqu'une erreur lors de l'appel à l'API entreprise est survenue"""

    logger.error("[API EXTERNES][CTRL] Une erreur lors de l'appel à l'API entreprise est survenue")

    err = ApiError(
        code=CODE_CALL_FAILED,
        message="Une erreur de l'API entreprise est survenue",
        remote_errors=error.errors,
    )
    dict = dataclasses.asdict(err)
    return dict


@api.errorhandler(InvalidTokenError)
@api.response(500, "Internal Server Error", model=ApiError.schema_model(api))
def handle_invalid_token_error(error):
    """Lorsque que le token DS est invalide"""

    return dataclasses.asdict(ApiError(code=CODE_INVALID_TOKEN, message="Le token sélectionné est invalide"))


@api.errorhandler(UnauthorizedOnDemarche)
@api.response(500, "Internal Server Error", model=ApiError.schema_model(api))
def handle_unauthorized_on_demarche(error):
    """Lorsque que le token DS sélectionné ne permet pas d'accéder aux données de l'API"""

    return dataclasses.asdict(
        ApiError(
            code=CODE_UNAUTHORIZED_ON_DEMARCHE,
            message="Vous n'avez pas les droits pour récupérer les données de cette démarche",
        )
    )


@api.errorhandler(DemarcheNotFound)
@api.response(500, "Internal Server Error", model=ApiError.schema_model(api))
def handle_demarche_not_found(error):
    """Lorsque la démarche demandée n'existe pas"""
    
    return dataclasses.asdict(ApiError(code=CODE_DEMARCHE_NOT_FOUND, message="Numéro de démarche inconnu"))


@api.errorhandler(Exception)
@api.response(500, "Internal Server Error", model=ApiError.schema_model(api))
def handle_generic(error):
    """Lorsqu'une erreur 500 vers la ressource externe est survenue"""

    logger.error("[API EXTERNES][CTRL] Une erreur est survenue")

    err = ApiError(
        code=CODE_UNKNOWN,
        message="Une erreur inconnue est survenue",
    )

    dict = dataclasses.asdict(err)
    return dict
