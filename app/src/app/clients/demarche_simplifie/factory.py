import functools
import logging

import requests
from flask import current_app

from app.clients.demarche_simplifie.errors import InvalidTokenError, UnauthorizedOnDemarche, DemarcheNotFound


class ApiDemarcheSimplifie:
    def __init__(self, token, url) -> None:
        self._token = token
        self._url = url

    def do_post(self, data) -> dict:
        headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
        answer = requests.post(url=self._url, headers=headers, data=data)

        if answer.status_code == 403:
            raise InvalidTokenError
        elif len(answer.json().get("errors") or "") > 0:
            error_message = answer.json().get("errors")[0].get("message")
            if error_message == "An object of type Demarche was hidden due to permissions":
                raise UnauthorizedOnDemarche
            elif error_message == "Demarche not found":
                raise DemarcheNotFound
        else:
            answer.raise_for_status()
        return answer.json()


def make_api_demarche_simplifie(token) -> ApiDemarcheSimplifie:
    """Fabrique un client API pour l'api demarche simplifie"""

    try:
        config = current_app.config["API_DEMARCHE_SIMPLIFIE"]

        url = config["URL"]

    except KeyError as e:
        logging.warning("Impossible de trouver la configuration de l'API demarche simplifie.", exc_info=e)
        return None

    return ApiDemarcheSimplifie(token, url)


@functools.cache
def get_or_make_api_demarche_simplifie(token) -> ApiDemarcheSimplifie:
    return make_api_demarche_simplifie(token)
