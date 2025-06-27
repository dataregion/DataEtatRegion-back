import functools
import logging
from flask import current_app

from api_entreprise import ApiEntreprise, ContextInfo, Config

from .ratelimiter import _make_rate_limiter


def _make_api_entreprise_from_config(config_key: str) -> ApiEntreprise | None:
    """Fabrique un client API à partir d'une clé de configuration Flask."""
    timeout = 5
    try:
        config = current_app.config[config_key]

        url = config["URL"]
        token = config["TOKEN"]
        context = config["CONTEXT"]
        recipient = config["RECIPIENT"]
        object = config["OBJECT"]

        timeout = int(config.get("TIMEOUT_SECONDS", timeout))
    except KeyError as e:
        logging.warning(
            f"Impossible de trouver la configuration de l'API entreprise ({config_key}).",
            exc_info=e,
        )
        return None

    api_config = Config(
        url,
        token,
        ContextInfo(context=context, recipient=recipient, object=object),
        _make_rate_limiter(config_key),
    )
    api_config.timeout_s = timeout

    return ApiEntreprise(api_config)


def make_api_entreprise() -> ApiEntreprise | None:
    """Fabrique un client API pour l'API entreprise."""
    return _make_api_entreprise_from_config("API_ENTREPRISE")


def make_api_entreprise_batch() -> ApiEntreprise | None:
    """Fabrique un client API pour l'API entreprise utilisable en mode batch."""
    if "API_ENTREPRISE_BATCH" not in current_app.config:
        return make_api_entreprise()
    return _make_api_entreprise_from_config("API_ENTREPRISE_BATCH")


@functools.cache
def get_or_make_api_entreprise() -> ApiEntreprise | None:
    return make_api_entreprise()


@functools.cache
def get_or_make_api_entreprise_batch() -> ApiEntreprise | None:
    return make_api_entreprise_batch()
