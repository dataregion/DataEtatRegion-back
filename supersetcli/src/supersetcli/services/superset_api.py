import functools
import json
import logging
from typing import Optional, Dict, Any
import requests

from supersetcli.services.errors import ApiSupersetError, UserNotFound


def _handle_httperror(response: requests.Response):
    logging.error(f"HTTP Error: {response.status_code} - {response.text}")
    raise ApiSupersetError(response.text)

def _handle_error_superset_api(func):
    """
    Decorator to handle Superset API errors.
    """
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            response: requests.Response = e.response
            _handle_httperror(response)
    return inner



class SupersetApiService:
    def __init__(self, server: str, username: str = None, password: str = None):
        """
        Initializes a Superset API client.

        Parameters:
            - server: Superset server URL (e.g., "https://superset.nocode.csm.ovh")
            - username: Username for authentication
            - password: Password for authentication
        """
        self.server = server.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.csrf_token: Optional[str] = None

    def set_credentials(self, username: str, password: str):
        """
        Sets or updates authentication credentials.

        Parameters:
            - username: Username for authentication
            - password: Password for authentication
        """
        self.username = username
        self.password = password
        # Reset tokens when credentials change
        self.access_token = None
        self.csrf_token = None

    @_handle_error_superset_api
    def _authenticate(self):
        """
        Authenticates with Superset and retrieves access token and CSRF token.
        This method is called automatically before API calls if tokens are not set.
        """
        if not self.username or not self.password:
            raise ValueError("Username and password must be set before making API calls")

        # 1. Login to get access token
        login_url = f"{self.server}/api/v1/security/login"
        login_data = {
            "username": self.username,
            "password": self.password,
            "provider": "db",
            "refresh": True
        }

        logging.debug(f"Authenticating user {self.username}")
        response = self.session.post(login_url, json=login_data)
        response.raise_for_status()
        self.access_token = response.json()["access_token"]

        # 2. Get CSRF token
        csrf_url = f"{self.server}/api/v1/security/csrf_token/"
        csrf_response = self.session.get(
            csrf_url,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        csrf_response.raise_for_status()
        self.csrf_token = csrf_response.json()["result"]

        logging.debug("Authentication successful")

    @_handle_error_superset_api
    def _call(self, uri: str, method: str = "GET", prefix: str = "/api/v1/", 
              json_data: Optional[Dict] = None, params: Optional[Dict] = None,
              auto_auth: bool = True) -> Any:
        """
        Makes a Superset REST API call.

        Parameters:
            - uri: API endpoint URI (without prefix)
            - method: HTTP method (GET, POST, PUT, DELETE)
            - prefix: API prefix (default: "/api/v1/")
            - json_data: JSON data for POST/PUT requests
            - params: Query parameters
            - auto_auth: Automatically authenticate if tokens are not set

        Returns the JSON response from the API.
        """
        # Authenticate if tokens are not set
        if auto_auth and (not self.access_token or not self.csrf_token):
            self._authenticate()

        full_url = f"{self.server}{prefix}{uri}"
        logging.debug(f"Sending {method} request to {full_url}")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-CSRFToken": self.csrf_token,
            "Referer": self.server
        }

        data = json.dumps(json_data).encode("utf8") if json_data is not None else None

        response = self.session.request(
            method,
            full_url,
            data=data,
            headers=headers,
            params=params
        )

        response.raise_for_status()
        return response.json()

    def get_or_create_dataset(
        self,
        database_id: int,
        table_name: str,
        schema: str,
        catalog: str,
        always_filter_main_dttm: bool = False,
        normalize_columns: bool = False,
        template_params: str = ""
    ) -> int:
        """
        Creates or retrieves a dataset in Superset.

        Parameters:
            - database_id: ID of the database
            - table_name: Name of the table
            - schema: Schema name
            - catalog: Catalog name (optional)
            - always_filter_main_dttm: Whether to always filter main datetime
            - normalize_columns: Whether to normalize column names
            - template_params: Template parameters

        Returns the API response containing the dataset information.
        """
        dataset_data = {
            "database_id": database_id,
            "table_name": table_name,
            "schema": schema,
            "catalog": catalog,
            "always_filter_main_dttm": always_filter_main_dttm,
            "normalize_columns": normalize_columns,
            "template_params": template_params
        }

        logging.debug(f"Creating/retrieving dataset {table_name} in schema {schema}")

        response = self._call(
            "dataset/get_or_create",
            method="POST",
            json_data=dataset_data
        )
        table_id = response["result"]["table_id"]
        logging.debug(f"Dataset table_id create: {table_id}")
        
        return table_id


    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """
        Searches for a user by username and returns their ID.

        Parameters:
            - username: Username to search for

        Returns the user ID if found, otherwise raises UserNotFound exception.
        """
        search = {
            "columns": ["id"],
            "filters": [
                {
                    "col": "username",
                    "opr": "eq",
                    "value": username
                }
            ]
        }

        logging.debug(f"Searching for user with username: {username}")

        response = self._call(
            "security/users/",
            method="GET",
            params={"q": json.dumps(search)}
        )

        if response.get("count", 0) > 0 and response.get("result"):
            user_id = response["result"][0]["id"]
            logging.debug(f"Found user {username} with ID: {user_id}")
            return user_id
        
        logging.warning(f"User {username} not found")
        raise UserNotFound()

    def set_dataset_owners(self, dataset_id: int, owner_ids: list[int]) -> Dict[str, Any]:
        """
        Sets the owners of a dataset.

        Parameters:
            - dataset_id: ID of the dataset
            - owner_ids: List of user IDs to set as owners

        Returns the updated dataset information.
        """
        update_data = {
            "owners": owner_ids
        }

        logging.debug(f"Setting owners {owner_ids} for dataset {dataset_id}")

        response = self._call(
            f"dataset/{dataset_id}",
            method="PUT",
            json_data=update_data
        )

        logging.debug(f"Dataset {dataset_id} owners updated successfully")
        return response

