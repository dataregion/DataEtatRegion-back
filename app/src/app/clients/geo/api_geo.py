import logging
import os

import requests

from flask import current_app

from models.entities.refs.Commune import Commune

LOGGER = logging.getLogger()

proxies = None
if os.environ.get("HTTP_PROXY") and os.environ.get("HTTPS_PROXY"):
    proxies = {"http": os.environ.get("HTTP_PROXY"), "https": os.environ.get("HTTPS_PROXY")}


class ApiGeoException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_info_commune(commune: Commune):
    api_geo = current_app.config["API_GEO"]

    response = requests.get(
        f"{api_geo}/communes/{commune.code}?fields=nom,epci,codeDepartement,departement,codeRegion,region&format=json",
        proxies=proxies,
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise ApiGeoException(f"Commune introuvable {commune.code}")
