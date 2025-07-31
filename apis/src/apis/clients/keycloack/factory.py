import functools

from keycloak import KeycloakAdmin, KeycloakOpenID

from models.exceptions import ConfigurationException

from apis.config import config


class KeycloakConfigurationException(ConfigurationException):
    """Exception raised when there is an error building the KeycloakAdmin client.

    Attributes:
        message (str): The message describing the error.
    """

    def __init__(self):
        super().__init__(configuration_key="Keycloak")


def make_keycloack_admin() -> KeycloakAdmin:
    """Builds a KeycloakAdmin client using the Flask app's configuration.

    Returns:
        KeycloakAdmin: The KeycloakAdmin client.

    Raises:
        KeycloakAdminException: If the Flask app's configuration is missing required values.
    """
    if "KEYCLOAK_ADMIN" not in config:
        raise KeycloakConfigurationException()

    config_keycloak = config["KEYCLOAK_ADMIN"]
    if (
        "URL" not in config_keycloak
        or "SECRET_KEY" not in config_keycloak
        or "REALM" not in config_keycloak
    ):
        raise KeycloakConfigurationException()

    return KeycloakAdmin(
        server_url=config["URL"],
        realm_name=config["REALM"],
        client_secret_key=config["SECRET_KEY"],
    )


@functools.cache
def make_or_get_keycloack_admin() -> KeycloakAdmin:
    return make_keycloack_admin()


def make_keycloack_openid() -> KeycloakOpenID:
    """Builds a KeycloakOpenID client using the Flask app's configuration.

    Returns:
        KeycloakOpenID: The KeycloakOpenIDConnection client.

    Raises:
        KeycloakAdminException: If the Flask app's configuration is missing required values.
    """
    if "KEYCLOAK_OPENID" not in config:
        raise KeycloakConfigurationException()

    config_keycloak = config["KEYCLOAK_OPENID"]
    if (
        "URL" not in config_keycloak
        or "REALM" not in config_keycloak
        or "CLIENT_ID" not in config_keycloak
    ):
        raise KeycloakConfigurationException()

    return KeycloakOpenID(
        server_url=config_keycloak["URL"],
        realm_name=config_keycloak["REALM"],
        client_id=config_keycloak["CLIENT_ID"],
        client_secret_key=(
            config_keycloak["SECRET_KEY"] if "SECRET_KEY" in config_keycloak else None
        ),
    )


@functools.cache
def make_or_get_keycloack_openid() -> KeycloakOpenID:
    return make_keycloack_openid()
