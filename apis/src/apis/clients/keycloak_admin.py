"""Client Keycloak Admin pour la recherche d'utilisateurs et la gestion Keycloak."""

import functools
import logging

from keycloak import KeycloakAdmin

from apis.config.current import get_config
from models.exceptions import BadRequestError


logger = logging.getLogger(__name__)


class KeycloakAdminError(BadRequestError):
    """Exception levée en cas d'erreur de configuration ou d'utilisation du client Keycloak Admin."""

    def __init__(self, message: str = "Erreur de configuration Keycloak Admin"):
        super().__init__(api_message=message)


def make_keycloak_admin() -> KeycloakAdmin:
    """Crée un client KeycloakAdmin en utilisant la configuration du module apis.

    Returns:
        KeycloakAdmin: Le client KeycloakAdmin configuré.

    Raises:
        KeycloakAdminError: Si la configuration est manquante ou invalide.
    """
    try:
        config = get_config()
        kc_config = config.keycloak_administrator

        if not kc_config.url or not kc_config.realm or not kc_config.secret_key:
            raise KeycloakAdminError("Configuration Keycloak incomplète (url, realm ou secret_key manquant)")

        return KeycloakAdmin(
            server_url=kc_config.url,
            realm_name=kc_config.realm,
            client_secret_key=kc_config.secret_key,
            verify=True,
        )
    except Exception as e:
        logger.error(f"Erreur lors de la création du client Keycloak Admin: {e}")
        raise KeycloakAdminError(f"Impossible de créer le client Keycloak Admin: {str(e)}")


@functools.cache
def get_keycloak_admin() -> KeycloakAdmin:
    """Retourne une instance unique (cached) du client KeycloakAdmin.

    Returns:
        KeycloakAdmin: L'instance cachée du client KeycloakAdmin.

    Raises:
        KeycloakAdminError: Si la création du client échoue.
    """
    return make_keycloak_admin()
