from typing import Iterable
from services.utils import wrap_all_ex_to

from apis.shared.exceptions import InvalidTokenError, NoCurrentRegion


class ConnectedUser:
    """
    Utilisateur connecté à l'application.
    Wrapper autour d'un token JWT décodé.
    """

    def __init__(self, token: dict):
        self.token = token or {}

        self._current_roles = None
        self._current_region = None
        self._username = None
        self._email = None
        self._name = None
        self._sub = None
        self._azp = None

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
        if self._current_region is None:
            self._current_region = self._retrieve_token_region()
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
    def _retrieve_token_region(self):
        region = self.token.get("region")
        if not region:
            raise NoCurrentRegion()
        return region

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
