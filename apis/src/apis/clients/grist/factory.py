import functools
import logging

from gristcli.gristservices.grist_api import GrisApiService
from gristcli.gristservices.users_grist_service import (
    UserGristDatabaseService,
    UserScimService,
)

from apis.config import config
from apis.shared.exceptions import ConfigurationException


class GristConfiguationException(ConfigurationException):
    """Exception raised when there is an error building the Grist client.

    Attributes:
        message (str): The message describing the error.
    """

    def __init__(self):
        super().__init__(configuration_key="Grist")


def make_grist_database_client() -> UserGristDatabaseService:
    """Builds a UserGristDatabaseService client using the Flask app's configuration.

    Returns:
        UserGristDatabaseService: The UserGristDatabaseService client.
    """
    config_grist = config.get("GRIST", {})
    url_grist_db = config_grist.get("DATABASE_URL", None)

    if url_grist_db is None:
        logging.error("[GRIST] Missing DATABASE_URL in GRIST configuration")
        raise GristConfiguationException()

    return UserGristDatabaseService(url_grist_db)


def make_grist_scim_client() -> UserScimService:
    """Builds a UserScimService client using the Flask app's configuration.

    Returns:
        UserScimService: The UserScimService client.
    """
    config_grist = config.get("GRIST", {})
    url = config_grist.get("SERVEUR_URL", None)
    token = config_grist.get("TOKEN_SCIM", None)

    if url is None or token is None:
        logging.error(
            "[GRIST] Missing SERVEUR_URL or TOKEN_SCIM in GRIST configuration"
        )
        raise GristConfiguationException()

    return UserScimService(url, token)


def make_grist_api_client(token: str) -> GrisApiService:
    config_grist = config.get("GRIST", {})
    url = config_grist.get("SERVEUR_URL", None)

    if url is None:
        logging.error("[GRIST] Missing DATABASE_URL in GRIST configuration")
        raise GristConfiguationException()

    return GrisApiService(url, token)


@functools.cache
def make_or_get_grist_database_client() -> UserGristDatabaseService:
    return make_grist_database_client()


@functools.cache
def make_or_get_grist_scim_client() -> UserScimService:
    return make_grist_scim_client()
