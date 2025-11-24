# Header pour le token
import secrets
from fastapi import Security
from fastapi.security import APIKeyHeader
from apis.shared.exceptions import InvalidTokenError

from apis.config.current import get_config


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)):  # type: ignore
    """
    Vérifie que le token API est valide.
    Utilise secrets.compare_digest pour éviter les timing attacks.
    """
    if not secrets.compare_digest(api_key, get_config().token_for_grist_plugins):
        raise InvalidTokenError(api_message="Token validation failed")
    return api_key
