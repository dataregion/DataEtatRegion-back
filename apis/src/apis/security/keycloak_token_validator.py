from authlib.jose import jwt, JsonWebKey
import logging
from fastapi import Depends
import requests

from fastapi.security import OAuth2PasswordBearer

from models.connected_user import ConnectedUser
from apis.config.Config import Config
from apis.config.current import get_config
from apis.shared.exceptions import InvalidTokenError

_instance = None


class KeycloakTokenValidator:
    @staticmethod
    def get_application_instance():
        global _instance
        if _instance is None:
            config = get_config()
            ktv = KeycloakTokenValidator(config)
            _instance = ktv
        return _instance

    def __init__(self, config: Config):
        self.issuer = f"{config.keycloak_openid.url}/realms/{config.keycloak_openid.realm}"
        self.jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{self.issuer}/protocol/openid-connect/token")
        self.algorithms = ["RS256"]
        self._jwk_set = None

        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _get_jwk_set(self):
        if self._jwk_set is None:
            response = requests.get(self.jwks_url)
            response.raise_for_status()
            self._jwk_set = JsonWebKey.import_key_set(response.json())
        return self._jwk_set

    def validate_token(self, token: str) -> ConnectedUser:
        try:
            jwk_set = self._get_jwk_set()
            claims = jwt.decode(
                token,
                key=jwk_set,
                claims_options={
                    "iss": {"essential": True, "value": self.issuer},
                    "exp": {"essential": True},
                },
            )
            claims.validate()
        except Exception as e:
            _ex = InvalidTokenError(api_message="Token validation failed")
            raise _ex from e

        connected_user = ConnectedUser(dict(claims))
        return connected_user

    def get_connected_user(self):
        """Récupère l'utilisateur connecté. Lève une exception si le token est invalide ou l'utilisateur n'a pas les droits d'accès basiques au service."""

        async def _wrapped(token: str = Depends(self.oauth2_scheme)) -> ConnectedUser:
            connected_user = self.validate_token(token)
            connected_user.check_has_access_rights()
            return connected_user

        return _wrapped
