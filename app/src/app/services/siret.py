from api_entreprise import ApiEntreprise

from flask import current_app
from services.clients.geo.api_geo import ApiGeoClient

from app.clients.entreprise import get_or_make_api_entreprise_batch
from services.refs.siret import UpdateRefSiretService


def api_geo_client():
    api_geo_url = current_app.config["API_GEO"]
    return ApiGeoClient(api_geo_url)


class AppUpdateRefSiretService(UpdateRefSiretService):
    """Service de mise à jour des référentiels siret"""

    def __init__(self, api_entreprise: ApiEntreprise, api_geo: ApiGeoClient) -> None:
        super().__init__(api_entreprise, api_geo)

    @staticmethod
    def create_for_app() -> "AppUpdateRefSiretService":
        """Crée une instance de UpdateRefSiretService pour l'application flask"""
        api_entreprise_batch = get_or_make_api_entreprise_batch()
        api_geo = api_geo_client()
        return AppUpdateRefSiretService(
            api_entreprise_batch,
            api_geo,
        )
