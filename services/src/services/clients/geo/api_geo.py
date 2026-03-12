import logging

import requests

from models.entities.refs.Commune import Commune

LOGGER = logging.getLogger()


class ApiGeoClient:
    def __init__(self, api_geo_url: str):
        self._api_geo_url = api_geo_url

    def get_info_commune(self, commune: Commune):
        api_geo = self._api_geo_url

        response = requests.get(
            f"{api_geo}/communes/{commune.code}?fields=nom,epci,codeDepartement,departement,codeRegion,region&format=json",
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise ApiGeoException(f"Commune introuvable {commune.code}")


class ApiGeoException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
