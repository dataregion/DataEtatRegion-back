import json
import logging
import requests


class GrisApiService:
    def __init__(self, server: str, token: str = None):
        """
        Initialse Un client Grist

        Parameters:
            - server : Url du serveur grist
            - token : token de l'utilisateur ayant le droit sur les service SCIM de grist
        """
        self.server = server
        self.token = token

    def set_token(self, token):
        self.token = token

    def _call(self, uri, method="GET", prefix="/api/", json_data=None, headers={}):
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
                "Accept": headers.get("accept", "application/json"),
                "Content-Type": headers.get("content-type", "application/json"),
            },
        )

        answer.raise_for_status()
        answer_json = answer.json()
        return answer_json

    def get_orgs(self):
        resp = self._call("orgs")
        return resp
