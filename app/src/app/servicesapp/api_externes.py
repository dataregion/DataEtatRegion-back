import logging

from app.clients.data_subventions import get_or_make_app_api_subventions_client
from app.clients.entreprise import (
    get_or_make_api_entreprise,
    get_or_make_api_entreprise_batch,
    ApiEntrepriseClientError,
)
from app.models.apis_externes.entreprise import InfoApiEntreprise
from app.models.apis_externes.subvention import InfoApiSubvention


def _siren(siret: str):
    return siret[0:9]


class ApisExternesService:
    """Service qui construit les informations provenant des API externes"""

    def __init__(self) -> None:
        self.api_entreprise = get_or_make_api_entreprise()
        self.api_entreprise_batch = get_or_make_api_entreprise_batch()
        self.api_subvention = get_or_make_app_api_subventions_client()

    def subvention(self, siret: str):
        subventions = self.api_subvention.get_subventions_pour_etablissement(siret)
        contacts = self.api_subvention.get_representants_legaux_pour_etablissement(siret)

        return InfoApiSubvention(subventions=subventions, contacts=contacts)

    def entreprise(self, siret: str, use_batch=False) -> InfoApiEntreprise:

        _api = self.api_entreprise_batch if use_batch else self.api_entreprise
        donnees_etab = _api.donnees_etablissement(siret)

        #
        # TODO: Verrue le temps d'avoir notre compte API entreprise ou implémenter l'api entreprise
        # avec les droits suffisants
        #
        # ca = self.api_entreprise.chiffre_d_affaires(siret)
        ca: list = []
        ca_indispo = False

        tva = None
        tva_indispo = False
        rge = []
        rge_indispo = False
        qualibat = None
        qualibat_indispo = False

        if not use_batch:
            siren = _siren(siret)

            try:
                tva = _api.numero_tva_intercommunautaire(siren)
            except ApiEntrepriseClientError as e:
                tva_indispo = True
                logging.exception(e)
            try:
                rge = _api.certifications_rge(siret)
            except ApiEntrepriseClientError as e:
                rge_indispo = True
                logging.exception(e)

            try:
                qualibat = _api.certification_qualibat(siret)
            except ApiEntrepriseClientError as e:
                qualibat_indispo = True
                logging.exception(e)

        return InfoApiEntreprise(
            donnees_etablissement=donnees_etab,
            tva_indispo=tva_indispo,
            tva=tva,
            chiffre_d_affaires_indispo=ca_indispo,
            chiffre_d_affaires=ca,
            certifications_rge_indispo=rge_indispo,
            certifications_rge=rge,
            certification_qualibat_indispo=qualibat_indispo,
            certification_qualibat=qualibat,
        )
