import functools
from app.exceptions.exceptions import ConfigurationException
from gristcli.gristservices.users_service import UserDatabaseService, UserScimService
from flask import current_app
import logging


class GristConfiguationException(ConfigurationException):
    """Exception raised when there is an error building the Grist client.

    Attributes:
        message (str): The message describing the error.
    """

    def __init__(self):
        super().__init__(configuration_key="Grist")


def make_grist_database_client() -> UserDatabaseService:
    """Builds a UserDatabaseService client using the Flask app's configuration.

    Returns:
        UserDatabaseService: The UserDatabaseService client.
    """
    config_grist = current_app.config.get("GRIST", {})
    url_grist_db = config_grist.get("DATABASE_URL", None)

    if url_grist_db is None:
        logging.error("[GRIST] Missing DATABASE_URL in GRIST configuration")
        raise GristConfiguationException()

    return UserDatabaseService(url_grist_db)


def make_grist_scim_client() -> UserScimService:
    """Builds a UserScimService client using the Flask app's configuration.

    Returns:
        UserScimService: The UserScimService client.
    """
    config_grist = current_app.config.get("GRIST", {})
    url = config_grist.get("SERVEUR_URL", None)
    token = config_grist.get("TOKEN_SCIM", None)

    if url is None or token is None:
        logging.error("[GRIST] Missing SERVEUR_URL or TOKEN_SCIM in GRIST configuration")
        raise GristConfiguationException()

    return UserScimService(url, token)


@functools.cache
def make_or_get_grist_database_client() -> UserDatabaseService:
    return make_grist_database_client()


@functools.cache
def make_or_get_grist_scim_client() -> UserScimService:
    return make_grist_scim_client()
