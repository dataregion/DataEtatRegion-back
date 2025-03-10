from app.exceptions.exceptions import ValidTokenException
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
import jwt
import logging


class KeycloakIntrospectTokenValidator(IntrospectTokenValidator):
    def __init__(self, jwks_endpoint, realm, client_id):
        self.jwks_url = jwks_endpoint
        self.realm = realm
        self.client_id = client_id
        self.jwks_client = jwt.PyJWKClient(self.jwks_url)
        super().__init__(None)

    def introspect_token(self, token: str) -> dict:
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)

        try:
            valid_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
            )
            if "username" not in valid_token and "preferred_username" in valid_token:
                valid_token["username"] = valid_token["preferred_username"]
            valid_token["active"] = True
        except jwt.PyJWTError:
            logging.debug("[PyJWTError] Error Token reçu non valide")
            raise ValidTokenException()

        return valid_token


auth = ResourceProtector()
