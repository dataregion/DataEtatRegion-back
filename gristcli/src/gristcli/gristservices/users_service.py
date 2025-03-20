import secrets
from sqlalchemy import create_engine, text
import requests, logging
import json

from gristcli.gristservices.errors import TokenNotFound
from gristcli.gristservices.handlers import _handle_error_grist_api
from gristcli.models import UserGrist


class UserDatabaseService:
    def __init__(self, database_url):
        """Initialise le service avec un moteur SQLAlchemy."""
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def get_or_create_api_token(self, id: int):
        """
        Récupère le token de l"utilisateur à partir d'un id
        """
        logging.debug(f"Retrieve API key for user {id}")
        with self.engine.connect() as connection:
            result = connection.execute(
                text("SELECT api_key FROM users WHERE id = :id"), {"id": id}
            )
            key = result.mappings().first()
        token = key.get("api_key", None)
        if token is None:
            token = secrets.token_hex(20)
            logging.debug(f"Api key not found for user {id}. We create one !")
            if self._update_api_key(id, token):
                return token
            else:
                raise TokenNotFound(id)
        return token

    def _update_api_key(self, user_id: int, new_api_key: str):
        """Met à jour la colonne api_key pour un utilisateur donné."""
        query = text("UPDATE users SET api_key = :api_key WHERE id = :id")
        with self.engine.connect() as connection:
            result = connection.execute(query, {"api_key": new_api_key, "id": user_id})
            connection.commit()
        return result.rowcount > 0


class UserScimService:
    def __init__(self, server: str, token: str):
        """
        Initialse Un client Grist pour le endpoint scim (https://support.getgrist.com/api/#tag/scim)

        Parameters:
            - server : Url du serveur grist
            - token : token de l'utilisateur ayant le droit sur les service SCIM de grist
        """
        self.server = server
        self.token = token

    def _call(self, uri, method="GET", prefix="/api/scim/v2", json_data=None):
        """
        Rest call grist
        """
        full_url = self.server + prefix + uri
        logging.debug(f"sending {method} request to {full_url}")
        data = json.dumps(json_data).encode("utf8") if json_data is not None else None
        answer = requests.request(
            method,
            full_url,
            data=data,
            headers={
                "Authorization": "Bearer %s" % self.token,
                "Accept": "application/scim+json",
                "Content-Type": "application/scim+json",
            },
        )

        answer.raise_for_status()
        answer_json = answer.json()
        return answer_json

    @_handle_error_grist_api
    def search_user_by_username(self, username: str) -> UserGrist:
        """
        Recherche un user en fonction de son userName
        """
        query = f'?filter=userName eq "{username}"'
        resp = self._call("/Users" + query)
        resources = resp.get("Resources", [])
        if not resources:
            return None

        logging.debug(
            f"[GRIST] {len(resources)} user trouvé sur le username {username}"
        )
        user_data = resources[0]
        if len(resources) > 1:
            logging.warning(
                f"[GRIST] {len(resources)} user trouvés sur le username {username}. Récupération du premier id = {user_data.get("id")}"
            )
        return UserGrist(
            user_id=user_data.get("id"),
            username=user_data.get("userName"),
            display_name=user_data.get("displayName"),
            email=user_data.get("emails", [{}])[0].get("value"),
        )

    @_handle_error_grist_api
    def create_user(self, user: UserGrist) -> UserGrist:
        """
        Créer un utilisateur dans Grist et le retourne avec son id
        """
        user_create = self._call(
            "/Users", method="POST", json_data=user.to_scim_payload()
        )
        user_create = UserGrist(
            user_id=user_create.get("id"),
            username=user_create.get("userName"),
            display_name=user_create.get("displayName"),
            email=user_create.get("emails", [{}])[0].get("value"),
        )
        logging.debug(
            f"Create new User {user_create.username} with id {user_create.user_id}"
        )
        return user_create
