import secrets
from sqlalchemy import create_engine, text
import logging
from urllib.parse import quote


from gristcli.gristservices.errors import TokenNotFound
from gristcli.gristservices.grist_api import GrisApiService
from gristcli.gristservices.handlers import _handle_error_grist_api
from gristcli.models import UserGrist


class UserGristDatabaseService:
    def __init__(self, database_url):
        """Initializes the service with an SQLAlchemy engine."""
        self.engine = create_engine(database_url, pool_pre_ping=True)

    def search_userid_by_email(self, email: str) -> int | None:
        """Retrieve the user ID based on the email."""
        logging.debug(f"Retrieve user id from email {email}")
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT user_id FROM logins WHERE email = :email"), {"email": email})
            key = result.mappings().first()
        user_id = int(key.get("user_id", None)) if key else None
        return user_id

    def get_or_create_api_token(self, id: int):
        """
        Retrieves the API token for the user based on their ID
        """
        logging.debug(f"Retrieve API key for user {id}")
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT api_key FROM users WHERE id = :id"), {"id": id})
            key = result.mappings().first()
        token = key.get("api_key", None)
        if token is None:
            token = secrets.token_hex(20)
            logging.debug(f"Api key not found for user {id}. We create one!")
            if self._update_api_key(id, token):
                return token
            else:
                raise TokenNotFound(id)
        return token

    def _update_api_key(self, user_id: int, new_api_key: str):
        """Updates the api_key column for a given user."""
        query = text("UPDATE users SET api_key = :api_key WHERE id = :id")
        with self.engine.connect() as connection:
            result = connection.execute(query, {"api_key": new_api_key, "id": user_id})
            connection.commit()
        return result.rowcount > 0


class UserScimService(GrisApiService):
    @_handle_error_grist_api
    def _call(self, uri, method="GET", prefix="/api/scim/v2", json_data=None):
        """
        Makes a REST API call to Grist
        """
        headers = {
            "accept": "application/scim+json",
            "content-type": "application/scim+json",
        }
        return super()._call(uri, method, prefix=prefix, json_data=json_data, headers=headers)

    def search_user_by_username(self, username: str) -> UserGrist:
        """
        Searches for a user based on their username
        """
        filter_str = f'userName eq "{username}"'
        encoded_filter = quote(filter_str)
        query = f"?filter={encoded_filter}"
        resp = self._call("/Users" + query)
        resources = resp.get("Resources", [])
        if not resources:
            return None

        logging.debug(f"[GRIST] {len(resources)} user(s) found for username {username}")
        user_data = resources[0]
        if len(resources) > 1:
            logging.warning(
                f"[GRIST] {len(resources)} users found for username {username}. Returning the first user with id = {user_data.get('id')}"
            )
        return UserGrist(
            user_id=user_data.get("id"),
            username=user_data.get("userName"),
            display_name=user_data.get("displayName"),
            email=user_data.get("emails", [{}])[0].get("value"),
        )

    def create_user(self, user: UserGrist) -> UserGrist:
        """
        Creates a user in Grist and returns it with its ID
        """
        user_create = self._call("/Users", method="POST", json_data=user.to_scim_payload())
        user_create = UserGrist(
            user_id=user_create.get("id"),
            username=user_create.get("userName"),
            display_name=user_create.get("displayName"),
            email=user_create.get("emails", [{}])[0].get("value"),
        )
        logging.debug(f"Create new User {user_create.username} with id {user_create.user_id}")
        return user_create
