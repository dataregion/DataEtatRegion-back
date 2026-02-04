import logging
from typing import Iterable
from models.exceptions import ForbiddenError, InvalidTokenError, NoCurrentRegion
from models.utils import wrap_all_ex_to


class ConnectedUser:
    """
    Utilisateur connecté à l'application.
    Wrapper autour d'un token JWT décodé.
    """

    def __init__(self, token: dict):
        self.logger = logging.getLogger(__name__)

        self.token = token or {}

        self._current_roles = None
        self._current_region = None
        self._username = None
        self._email = None
        self._name = None
        self._sub = None
        self._azp = None

    def _get_resource_access_roles(self, azp: str) -> list:
        """Récupère les rôles du resource_access de manière sûre."""
        try:
            roles = self.token["resource_access"][azp]["roles"]
            return roles if isinstance(roles, list) else []
        except Exception as e:
            self.logger.warning(f"Token au mauvais format lors de la vérification de l'accès à {azp}", exc_info=e)
            return []

    def check_has_access_rights(self):
        """Vérifie que l'utilisateur connecté a les droits d'accès au service."""
        azp = self._retrieve_token_azp()
        roles = self._get_resource_access_roles(azp)

        if "users" not in roles:
            raise ForbiddenError("L'utilisateur n'a pas les droits d'accès au service.")

    def check_has_role(self, role: str):
        """Vérifie que l'utilisateur connecté a le rôle spécifié."""
        azp = self._retrieve_token_azp()
        roles = self._get_resource_access_roles(azp)

        if role not in roles:
            raise ForbiddenError(f"L'utilisateur n'a pas le rôle requis : {role}")

    def check_has_any_role(self, roles: list):
        """Vérifie que l'utilisateur connecté a l'un des rôles spécifiés."""
        azp = self._retrieve_token_azp()
        resource_roles = self._get_resource_access_roles(azp)

        if not any(role in resource_roles for role in roles):
            roles_str = " ou ".join(roles)
            raise ForbiddenError(f"L'utilisateur n'a pas l'un des rôles requis : {roles_str}")

    @property
    def roles(self):
        if self._current_roles is None:
            self._current_roles = self._retrieve_token_roles()
        return self._current_roles

    @property
    def azp(self):
        if self._azp is None:
            self._azp = self._retrieve_token_azp()
        return self._azp

    @property
    def current_region(self):
        """
        Retourne la région courante pour laquelle l'utlisateur a le droit de consultation.
        """
        if self._current_region is None:
            self._current_region = self._retrieve_connected_user_region()
        return self._current_region

    @property
    def username(self):
        if self._username is None:
            self._username = self._retrieve_token_username()
        return self._username

    @property
    def email(self):
        if self._email is None:
            self._email = self._retrieve_token_email()
        return self._email

    @property
    def name(self):
        if self._name is None:
            self._name = self._retrieve_token_name()
        return self._name

    @property
    def sub(self):
        if self._sub is None:
            self._sub = self._retrieve_token_sub()
        return self._sub

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_roles(self):
        roles = self.token.get("roles")
        assert isinstance(roles, Iterable), "Les rôles devraient être une liste"
        return [r.upper() for r in roles]

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_azp(self):
        azp = self.token.get("azp")
        assert isinstance(azp, str), "Le claim azp doit être une string"
        return azp

    @wrap_all_ex_to(NoCurrentRegion)
    def _retrieve_connected_user_region(self):
        """Récupère la region associé au role users du client courant (bretagne.budget, bretagne.qpv etc)"""

        azp = self._retrieve_token_azp()
        try:
            region = self.token["roles_meta"][azp]["users"]["region"]
            assert isinstance(region, str), "La région doit être une chaine de caractères"
            return region
        except Exception as e:
            self.logger.error("Impossible de récupérer la region courante.", exc_info=e)
            raise NoCurrentRegion()

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_username(self):
        return self.token["username"]

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_email(self):
        return self.token["email"]

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_name(self):
        return self.token["name"]

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_sub(self):
        return self.token["sub"]
