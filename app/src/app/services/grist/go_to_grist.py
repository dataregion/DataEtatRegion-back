from datetime import datetime
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

        workspaces = grist_api.get_personnal_workspace()
        if len(workspaces) == 0:
            logger.info("[GRIST] L'utilisateur n'a pas de workspace.")
            workspace_id = grist_api.create_workspace("Home")
            logger.debug(f"[GRIST] Création workspace Home {workspace_id}")
        else:
            logger.debug(f"[GRIST] Récupération du worskpace {workspaces[0].id}")
            workspace_id = workspaces[0].id

        docName = GristCliService._build_new_doc_name()
        logger.info(f"[GRIST] Création document {docName} dans le workspace {workspace_id}")
        docId = grist_api.create_doc_on_workspace(workspace_id, docName)
        logger.debug(f"[GRIST] Document {docId} créé")

        logger.debug(f"[GRIST] Création table budget dans le doc {docId} avec les données")
        # TODO mettre de vrai donnée Budget
        grist_api.new_table(
            docId,
            "budget",
            cols=[{"id": "ej", "label": "Numero ej"}, {"id": "montantAe", "label": " Montant Engagé"}],
            records=[{"ej": "121212112", "montantAe": 12}, {"ej": "99999", "montantAe": 12}],
        )

        logger.info(f"[GIRST] End Call go-to-grist for user {userConnected.username}")

    @staticmethod
    def _build_new_doc_name() -> str:
        now = datetime.now()
        date_formatee = now.strftime("%d/%m/%Y à %H:%M")
        return f"Export budget {date_formatee}"
