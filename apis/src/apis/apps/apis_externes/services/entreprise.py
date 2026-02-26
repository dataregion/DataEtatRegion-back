import logging
from services.apis_externes.clients.entreprise import ApiEntrepriseClientError
from services.apis_externes.models.InfoApiEntreprise import InfoApiEntreprise
from services.apis_externes.clients.entreprise.factory import make_api_entreprise


from apis.config.current import get_config

logger = logging.getLogger(__name__)

api_entreprise_info = get_config().api_entreprise
api_entreprise = make_api_entreprise(api_entreprise_info)

api_entreprise_info_batch = get_config().api_entreprise_batch
api_entreprise_batch = make_api_entreprise(api_entreprise_info_batch)


def _siren(siret: str):
    return siret[0:9]


def retrieve_entreprise_info(siret, use_batch=False) -> InfoApiEntreprise:
    _api = api_entreprise_batch if use_batch else api_entreprise

    assert _api is not None
    donnees_etablissement = _api.donnees_etablissement(siret)

    #
    # XXX: Verrue dû à notre compte API entreprise avec droits insuffisants
    # ca = self._api.chiffre_d_affaires(siret)
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
            logger.exception(e)
        try:
            rge = _api.certifications_rge(siret)
        except ApiEntrepriseClientError as e:
            rge_indispo = True
            logger.exception(e)

        try:
            qualibat = _api.certification_qualibat(siret)
        except ApiEntrepriseClientError as e:
            qualibat_indispo = True
            logger.exception(e)

    return InfoApiEntreprise(
        donnees_etablissement=donnees_etablissement,
        tva_indispo=tva_indispo,
        tva=tva,
        chiffre_d_affaires_indispo=ca_indispo,
        chiffre_d_affaires=ca,
        certifications_rge_indispo=rge_indispo,
        certifications_rge=rge,
        certification_qualibat_indispo=qualibat_indispo,
        certification_qualibat=qualibat,
    )
