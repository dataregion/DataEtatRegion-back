from dataclasses import dataclass
import logging
from services.apis_externes.clients.data_subventions.factory import make_app_api_subventions_client
from services.apis_externes.clients.data_subventions import Subvention, RepresentantLegal
from apis.config.current import get_config

logger = logging.getLogger(__name__)

ds_config = get_config().api_data_subventions
data_subventions_client = make_app_api_subventions_client(ds_config)


@dataclass
class InfoApiSubvention:
    """Informations qui proviennent de l'API subvention"""

    subventions: list[Subvention]
    contacts: list[RepresentantLegal]


def subvention(siret: str):
    subventions = data_subventions_client.get_subventions_pour_etablissement(siret)
    contacts = data_subventions_client.get_representants_legaux_pour_etablissement(siret)

    return InfoApiSubvention(subventions=subventions, contacts=contacts)
