import dataclasses

from app.models.apis_externes.error import (
    CODE_UNKNOWN,
    Error as ApiError,
    CODE_INVALID_TOKEN,
    CODE_DEMARCHE_NOT_FOUND,
    CODE_UNAUTHORIZED_ON_DEMARCHE,
)
from . import api
from . import logger
from ...clients.demarche_simplifie.errors import InvalidTokenError, UnauthorizedOnDemarche, DemarcheNotFound


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
