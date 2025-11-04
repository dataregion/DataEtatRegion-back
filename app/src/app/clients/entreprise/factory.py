import functools
import logging
from flask import current_app

from models.value_objects.api_entreprise_info import ApiEntrepriseInfo
from models.value_objects.ratelimiter_info import RateLimiterInfo, RedisConnectionInfo
from services.apis_externes.clients.entreprise.factory import make_api_entreprise as _make_api_entreprise
from api_entreprise import ApiEntreprise


def _ratelimiter_info_from_config(config_path: str):
    config = current_app.config[config_path]

    ratelimiter = config["RATELIMITER"]
    ratelimiter_redis = ratelimiter["REDIS"]

    limit = ratelimiter["LIMIT"]
    duration = ratelimiter["DURATION"]

    info = RateLimiterInfo(
        redis=RedisConnectionInfo(
            host=ratelimiter_redis["HOST"],
            port=ratelimiter_redis["PORT"],
            db=ratelimiter_redis["DB"],
        ),
        limit=limit,
        duration=duration,
    )

    return info


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

    info = ApiEntrepriseInfo(
        url=url,
        token=token,
        context=context,
        recipient=recipient,
        object=object,
        timeout_seconds=timeout,
    )
    ratelimiter_info = _ratelimiter_info_from_config(config_key)
    api_entreprise = _make_api_entreprise(info, ratelimiter_info)
    return api_entreprise


def make_api_entreprise_batch() -> ApiEntreprise | None:
    """Fabrique un client API pour l'API entreprise utilisable en mode batch."""
    return _make_api_entreprise_from_config("API_ENTREPRISE_BATCH")


@functools.cache
def get_or_make_api_entreprise_batch() -> ApiEntreprise | None:
    return make_api_entreprise_batch()
