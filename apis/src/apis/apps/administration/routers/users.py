from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends

from apis.clients.keycloack.factory import KeycloakConfigurationException, make_or_get_keycloack_admin
from apis.database import get_db
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{username:str}", summary="Retourne un utilisateur grâce au username")
@handle_exceptions
def find_user_by_username(username: str):
    if username is None or len(username) < 4:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            data=[],
        )
    try:
        keycloak_admin = make_or_get_keycloack_admin()
        query = {"briefRepresentation": True, "enabled": True, "search": username}
        users = keycloak_admin.get_users(query)

        return [{"username": user["username"]} for user in users], HTTPStatus.OK
    except KeycloakConfigurationException as admin_exception:
        return admin_exception.message, HTTPStatus.BAD_REQUEST