from authlib.integrations.flask_oauth2 import current_token


from models.exceptions import InvalidTokenError
from models.connected_user import ConnectedUser


def connected_user_from_current_token_identity():
    """Crée un utilisateur connecté d'aprés un id token

    Raises:
       InvalidTokenError
    """
    token = _current_token_identity()
    return ConnectedUser(token)  # pyright: ignore[reportArgumentType]


def _current_token_identity():
    token = current_token
    if token is None:
        raise InvalidTokenError("Aucun token présent.")
    return token
