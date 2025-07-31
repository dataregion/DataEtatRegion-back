import logging
import functools

from apis.clients.data_subventions.api_subventions import ApiSubventions
from apis.config import config


def make_app_api_subventions_client() -> ApiSubventions:
    """Fabrique un client API de DataSubvention

    Utilise la confiugration `API_DATA_SUBVENTIONS` de l'application.
    """
    try:
        config_subventions = config["API_DATA_SUBVENTIONS"]

        url = config_subventions["URL"]
        token = config_subventions["TOKEN"]
    except KeyError as e:
        logging.warning(
            "Impossible de trouver la confiugration de l'API subvention", exc_info=e
        )
        return None

    return ApiSubventions(token, url)


@functools.cache
def get_or_make_app_api_subventions_client() -> ApiSubventions:
    return make_app_api_subventions_client()
