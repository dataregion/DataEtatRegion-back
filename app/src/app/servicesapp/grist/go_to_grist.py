from datetime import datetime
import logging
import re
from typing import List
from app.clients.grist.factory import (
    make_grist_api_client,
    make_or_get_grist_database_client,
    make_or_get_grist_scim_client,
)
from app.servicesapp.grist import ParsingColumnsError
from models.connected_user import ConnectedUser

from gristcli.gristservices.users_grist_service import UserGristDatabaseService, UserScimService
from gristcli.models import UserGrist

logger = logging.getLogger(__name__)


class GristCliService:

    @staticmethod
    def send_request_to_grist(
        userConnected: ConnectedUser,
        data: List,
        userService: UserGristDatabaseService = make_or_get_grist_database_client(),
        userScimService: UserScimService = make_or_get_grist_scim_client(),
    ):
        logger.info(f"[GIRST] Start Call go-to-grist for user {userConnected.username}")

        logger.debug("[GRIST] Fetch Columns")
        columns, records = GristCliService._build_columns_and_records(data)

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
        grist_api.new_table(
            docId,
            "budget",
            cols=columns,
            records=records,
        )
        logger.info(f"[GIRST] End Call go-to-grist for user {userConnected.username}")

    @staticmethod
    def _build_new_doc_name() -> str:
        now = datetime.now()
        date_formatee = now.strftime("%d/%m/%Y à %H:%M")
        return f"Export budget {date_formatee}"

    @staticmethod
    def _build_columns_and_records(data) -> tuple:
        """
        Construit à la fois les colonnes et les records à partir des objets dans 'data'.
        Cette méthode génère une liste de colonnes (avec 'id' nettoyé et 'label' d'origine)
        et transforme les données en remplaçant les clés d'origine par les 'id' nettoyés correspondants.

        La méthode vérifie que toutes les lignes ont les mêmes clés et crée une liste de
        dictionnaires contenant 'id' et 'label' pour chaque colonne. Elle crée également
        les records en remplaçant les clés des objets par les identifiants nettoyés.

        :param data: Liste d'objets JSON (chaque objet est un dictionnaire avec des clés représentant
                    les colonnes). Les objets doivent avoir des clés identiques pour toutes les lignes.
        :return: Un tuple contenant deux éléments:
                - Une liste de dictionnaires avec 'id' (clé nettoyée) et 'label' (clé d'origine) pour chaque colonne.
                - Une liste de records (dictionnaires) où chaque clé est remplacée par son 'id' nettoyé,
                et les valeurs restent inchangées.

        :raises ParsingColumnsError: Si les objets dans 'data' n'ont pas les mêmes clés.
        :raises ValueError: Si 'data' est vide.
        """
        reference_keys = set(data[0].keys())

        for item in data:
            if set(item.keys()) != reference_keys:
                raise ParsingColumnsError()

        keys = list(reference_keys)
        columns = [{"id": GristCliService._clean_key(k), "label": k} for k in keys]
        mappings = {col["label"]: col["id"] for col in columns}

        records = []
        for item in data:
            record = {}
            for key, value in item.items():
                # Remplacer la clé d'origine par l'id nettoyé
                record[mappings.get(key, key)] = value  # Si la clé n'est pas trouvée, on garde la clé d'origine
            records.append(record)

        return columns, records

    @staticmethod
    def _clean_key(key: str) -> str:
        """
        Nettoie une clé en supprimant les caractères spéciaux et les espaces.
        Remplace les espaces par des underscores et met tout en minuscule.

        :param key: La clé originale
        :return: Une version nettoyée de la clé
        """
        key = key.lower()  # Convertir en minuscules
        key = re.sub(r"\s+", "_", key)  # Remplacer les espaces par des underscores
        key = re.sub(r"[^a-z0-9_]", "", key)  # Supprimer tout sauf lettres, chiffres et underscore
        return key
