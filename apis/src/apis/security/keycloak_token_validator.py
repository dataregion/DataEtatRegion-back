from authlib.jose import jwt, JsonWebKey, JoseError
import requests

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from apis.security.connected_user import ConnectedUser


class KeycloakTokenValidator:

    def __init__(self, config: dict):
        self.issuer = f"{config['KEYCLOAK_OPENID']['URL']}/realms/{config['KEYCLOAK_OPENID']['REALM']}"
        self.jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{self.issuer}/protocol/openid-connect/token")
        self.algorithms = ["RS256"]
        self._jwk_set = None

    def _get_jwk_set(self):
        if self._jwk_set is None:
            response = requests.get(self.jwks_url)
            response.raise_for_status()
            self._jwk_set = JsonWebKey.import_key_set(response.json())
        return self._jwk_set

    def validate_token(self, token: str) -> ConnectedUser:
        try:
            jwk_set = self._get_jwk_set()
            claims = jwt.decode(token, key=jwk_set, claims_options={
                "iss": {"essential": True, "value": self.issuer},
                "exp": {"essential": True},
            })
            claims.validate()
        except JoseError as e:
            raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")

        return ConnectedUser(dict(claims))

    def get_connected_user(self):
        async def _wrapped(token: str = Depends(self.oauth2_scheme)) -> ConnectedUser:
            return self.validate_token(token)
        return _wrapped
