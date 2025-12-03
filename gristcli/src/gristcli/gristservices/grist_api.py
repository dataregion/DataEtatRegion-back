import json
import logging
from typing import List
import requests

from gristcli.gristservices.handlers import _handle_error_grist_api
from gristcli.models import Record, Table, Workspace


class GrisApiService:
    def __init__(self, server: str, token: str = None):
        """
        Initializes a Grist client.

        Parameters:
            - server: Grist server URL
            - token: User's token with access to Grist SCIM services
        """
        self.server = server
        self.token = token

    def set_token(self, token):
        self.token = token

    @_handle_error_grist_api
    def _call(self, uri, method="GET", prefix="/api/", json_data=None, headers={}):
        """
        Makes a Grist REST API call.
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
                "Accept": headers.get("accept", "application/json"),
                "Content-Type": headers.get("content-type", "application/json"),
            },
        )

        answer.raise_for_status()
        answer_json = answer.json()
        return answer_json

    def get_personnal_workspace(self) -> List[Workspace]:
        """
        Fetches the user's personal workspace.

        Returns a list of Workspace objects.
        """
        api_response = self._call("orgs/docs/workspaces")
        projects = [Workspace(**data) for data in api_response]
        return projects

    def create_workspace(self, name: str) -> int:
        """
        Creates a new workspace.

        Parameters:
            - name: Name of the new workspace

        Returns the response from the API call.
        """
        resp = self._call("orgs/docs/workspaces", method="POST", json_data={"name": name})
        return resp

    def create_doc_on_workspace(self, workspaceId: int, docName: str):
        """
        Creates a document within a workspace.

        Parameters:
            - workspaceId: ID of the workspace
            - docName: Name of the new document

        Returns the response from the API call.
        """
        json_data = {"name": docName, "isPinned": False}
        return self._call(f"workspaces/{workspaceId}/docs", method="POST", json_data=json_data)

    def new_table(self, docId: str, tableId: str, cols: List[dict], records=None):
        """
        Creates a new table in a document with a defined list of columns.

        The `cols` parameter is a list of tuples containing a column ID and a label for each column.

        Example:
        [{'id': 'col_id', 'label': 'label col'}, {'id': 'col_id_2', 'label': 'label col 2'}]
        The `records` parameter contains the data to be inserted, if not None. It is a list of key-value lists where the key is the column ID and the value is the data value.

        Example:
        ```
            [
                {"col_id_1":"value of row 1 col 1", "col_id_2": "value of row 1 col 2"},
                {"col_id_1":"value of row 2 col 1", "col_id_2": "value of row 2 col 2"},
            ]
        ```

        Parameters:
            - docId: The document ID where the table will be created
            - tableId: The ID of the new table
            - cols: List of columns (Column objects)
            - records: Optional list of records to insert

        Returns an empty dictionary (or custom response if needed).
        """
        json_table = {
            "tables": [
                {
                    "id": tableId,
                    "columns": [{"id": c["id"], "fields": {"label": c["label"]}} for c in cols],
                }
            ]
        }
        logging.debug(f"Create table {tableId} {json_table}")

        response = self._call(f"docs/{docId}/tables", method="POST", json_data=json_table)
        table_create = response.get("tables")[0].get("id")
        logging.debug(f"Table id {table_create} create OK")

        if records is not None:
            logging.debug("Insert records in table")
            map_records = {"records": [{"fields": row} for row in records]}
            self._call(
                f"docs/{docId}/tables/{table_create}/records",
                method="POST",
                json_data=map_records,
            )

        return {}

    def get_tables_of_doc(self, docId: str) -> List[Table]:
        response = self._call(f"docs/{docId}/tables")
        tables = [Table(**data) for data in response["tables"]]
        return tables

    def get_records_of_table(self, docId: str, tableId: str) -> List[Record]:
        response = self._call(f"docs/{docId}/tables/{tableId}/records")
        records = [Record(**data) for data in response["records"]]
        return records
