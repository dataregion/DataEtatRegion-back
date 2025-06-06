from typing import Iterable
from authlib.integrations.flask_oauth2 import current_token


from ..exceptions.authentication import NoCurrentRegion

from ..exceptions.authentication import InvalidTokenError
from app.utilities.exhandling import wrap_all_ex_to


class ConnectedUser:
    """
    Utilisateur connecté à l'application.
    Basiquement un wrapper à g.current_token_identity
    """

    def __init__(self, token):
        self.token = token

        self._current_roles = None
        self._current_region = None
        self._username = None
        self._email = None
        self._name = None
        self._sub = None
        self._azp = None

    @property
    def roles(self):
        """Récupère les rôle actifs sur la région actuellement connectée"""
        if self._current_roles is None:
            self._current_roles = self._retrieve_token_roles()
        return self._current_roles

    @property
    def azp(self):
        """Récupère le claim 'azp' du token"""
        if self._azp is None:
            self._azp = self._retrieve_token_azp()
        return self._azp

    @property
    def current_region(self):
        """Récupère la region sur laquelle l'utilisateur est actuellement connecté"""
        if self._current_region is None:
            self._current_region = self._retrieve_token_region()
        return self._current_region

    @property
    def username(self):
        """Récupère l'username du token"""
        if self._username is None:
            self._username = self._retrieve_token_username()
        return self._username

    @property
    def email(self):
        """Récupère le mail du token"""
        if self._email is None:
            self._email = self._retrieve_token_email()
        return self._email

    @property
    def name(self):
        """Récupère le displayname du token"""
        if self._name is None:
            self._name = self._retrieve_token_name()
        return self._name

    @property
    def sub(self):
        """Récupère le claim 'sub' du token"""
        if self._sub is None:
            self._sub = self._retrieve_token_sub()
        return self._sub

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_roles(self):
        roles = self.token["roles"] if "roles" in self.token else None
        assert isinstance(roles, Iterable), "Les rôles devraient être une liste"
        if roles is not None:
            roles = [x.upper() for x in roles]
        return roles

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_azp(self):
        azp = self.token["azp"] if "azp" in self.token else None
        assert isinstance(azp, str), "Le claim azp doit être un string"
        return azp

    @wrap_all_ex_to(NoCurrentRegion)
    def _retrieve_token_region(self):
        region = self.token["region"]
        if region is None:
            raise NoCurrentRegion()
        return region

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_username(self):
        username = self.token["username"]
        if username is None:
            raise InvalidTokenError()
        return username

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_email(self):
        email = self.token["email"]
        if email is None:
            raise InvalidTokenError()
        return email

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_name(self):
        name = self.token["name"]
        if name is None:
            raise InvalidTokenError()
        return name

    @wrap_all_ex_to(InvalidTokenError)
    def _retrieve_token_sub(self):
        sub = self.token["sub"]
        if sub is None:
            raise InvalidTokenError()
        return sub

    @staticmethod
    def from_current_token_identity():
        """Crée un utilisateur connecté d'aprés un id token

        Returns:
            _type_: _description_

        Raises:
           InvalidTokenError
        """
        token = _current_token_identity()
        return ConnectedUser(token)


def _current_token_identity():
    token = current_token
    if token is None:
        raise InvalidTokenError("Aucun token présent.")
    return token
