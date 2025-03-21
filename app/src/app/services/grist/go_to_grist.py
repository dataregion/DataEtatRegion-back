import logging
from app.clients.grist.factory import (
    make_grist_api_client,
    make_or_get_grist_database_client,
    make_or_get_grist_scim_client,
)
from app.servicesapp.authentication.connected_user import ConnectedUser

from gristcli.gristservices.users_grist_service import UserGristDatabaseService, UserScimService
from gristcli.models import UserGrist

logger = logging.getLogger(__name__)


class GristCliService:

    @staticmethod
    def send_request_to_grist(
        userConnected: ConnectedUser,
        userService: UserGristDatabaseService = make_or_get_grist_database_client(),
        userScimService: UserScimService = make_or_get_grist_scim_client(),
    ):
        logger.info(f"[GIRST] Start Call go-to-grist for user {userConnected.username}")

        # check user exist
        logger.debug(f"[GIRST] {userConnected.username} exist in grist ?")

        user = userScimService.search_user_by_username(userConnected.username)
        if user is None:
            # SI non exist, create user
            logger.debug("[GIRST] No. We create users")

            user = userScimService.create_user(
                UserGrist(username=userConnected.username, email=userConnected.email, display_name=userConnected.name)
            )
            logger.debug(f"[GIRST] New user create with id {user.user_id}")

        # Recup token
        logger.debug(f"[GRIST] Get Api key for user {userConnected.username}")
        token = userService.get_or_create_api_token(user.user_id)

        grist_api = make_grist_api_client(token)

        logger.debug("[GRIST] Retrive token sucess")
        # TO-Do import data

        logger.info(f"[GIRST] End Call go-to-grist for user {userConnected.username}")
        return grist_api.get_orgs()
