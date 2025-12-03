import logging
import requests

from .models import Subvention, ActionProposee, RepresentantLegal
from .handlers import _handle_response_in_error

from ..utils import _dict_get_nested

LOGGER = logging.getLogger()


class ApiSubventions:
    def __init__(self, token, url) -> None:
        self._token = token
        self._url = url
        self._timeout = 10

    @_handle_response_in_error
    def get_representants_legaux_pour_etablissement(self, siret: str):
        url = f"{self._url}/etablissement/{siret}"
        auth_params = self._auth_params()
        answer = requests.get(url, params=auth_params, timeout=self._timeout)
        answer.raise_for_status()
        json = answer.json()
        return self._json_to_representants_legaux(json)

    @_handle_response_in_error
    def get_subventions_pour_etablissement(self, siret: str):
        url = f"{self._url}/etablissement/{siret}/subventions"
        auth_params = self._auth_params()
        answer = requests.get(url, params=auth_params, timeout=self._timeout)
        answer.raise_for_status()
        json = answer.json()
        return self._json_to_subventions(json)

    def _auth_params(self):
        return {"token": self._token}

    def _json_to_representants_legaux(self, json_dict) -> list[RepresentantLegal]:
        def map(raw):
            representant = RepresentantLegal(
                nom=_dict_get_nested(raw, "value", "nom"),  # type: ignore
                prenom=_dict_get_nested(raw, "value", "prenom"),  # type: ignore
                civilite=_dict_get_nested(raw, "value", "civilite"),  # type: ignore
                role=_dict_get_nested(raw, "value", "role"),  # type: ignore
                telephone=_dict_get_nested(raw, "value", "telephone"),  # type: ignore
                email=_dict_get_nested(raw, "value", "email"),  # type: ignore
            )
            return representant

        raws = _dict_get_nested(json_dict, "etablissement", "representants_legaux", default={})
        return [map(x) for x in raws]

    def _json_to_subventions(self, json_dict) -> list[Subvention]:
        def map(raw):
            raw_actions_proposee = _dict_get_nested(raw, "actions_proposee", default=[])

            subvention = Subvention(
                ej=_dict_get_nested(raw, "ej", "value"),  # type: ignore
                service_instructeur=_dict_get_nested(raw, "service_instructeur", "value"),  # type: ignore
                dispositif=_dict_get_nested(raw, "dispositif", "value"),  # type: ignore
                sous_dispositif=_dict_get_nested(raw, "sous_dispositif", "value"),  # type: ignore
                montant_demande=_dict_get_nested(raw, "montants", "demande", "value"),  # type: ignore
                montant_accorde=_dict_get_nested(raw, "montants", "accorde", "value"),  # type: ignore
                actions_proposees=[_parse_action_proposee(x) for x in raw_actions_proposee],
            )
            return subvention

        raws = json_dict["subventions"]
        return [map(x) for x in raws]


def _parse_action_proposee(dict) -> ActionProposee:
    return ActionProposee(
        intitule=_dict_get_nested(dict, "intitule", "value"),  # type: ignore
        objectifs=_dict_get_nested(dict, "objectifs", "value"),  # type: ignore
    )
