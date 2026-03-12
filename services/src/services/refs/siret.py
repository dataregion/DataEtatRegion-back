import logging
from typing import Callable

from api_entreprise import ApiEntreprise, ApiError

from sqlalchemy.orm import Session
from api_entreprise.models.donnees_etablissement import DonneesEtablissement
from services.clients.geo.api_geo import ApiGeoClient, ApiGeoException
from models.entities.refs.Commune import Commune
from models.entities.refs.Siret import Siret

logger = logging.getLogger(__name__)


ApiEntrepriseFactory = Callable[[], ApiEntreprise]


class UpdateRefSiretService:
    """Service de mise à jour des référentiels siret"""

    def __init__(self, api_entreprise: ApiEntreprise, api_geo: ApiGeoClient) -> None:
        self._api_entreprise = api_entreprise
        self._api_geo = api_geo

    def _map(self, siret: Siret, etablissement: DonneesEtablissement):
        categorie_juridique = etablissement.unite_legale.forme_juridique.code
        code_commune = etablissement.adresse.code_commune
        raison_sociale = etablissement.unite_legale.personne_morale_attributs.raison_sociale
        adresse = etablissement.adresse_postale_legere

        personne_phy_denomination = etablissement.unite_legale.personne_physique_attributs.denomination
        denomination = raison_sociale if raison_sociale is not None else personne_phy_denomination

        siret.categorie_juridique = categorie_juridique
        siret.code_commune = code_commune
        siret.denomination = denomination
        siret.adresse = adresse

    def check_siret(self, session: Session, siret):
        """Rempli les informations du siret via l'API entreprise

        Raises:
            LimitHitError: Si le ratelimiter de l'API entreprise est déclenché
        """
        if siret is not None:
            logger.info(f"[SERVICE][SIRET] Début check siret {siret}")

            existing_siret = session.query(Siret).filter_by(code=str(siret)).one_or_none()
            if existing_siret:
                logger.info(f"[SERVICE][SIRET] Siret {siret} déjà présent en base, aucune insertion nécessaire.")
            else:
                siret_entity = self.update_siret_from_api_entreprise(session, siret, insert_only=True)

                if siret_entity.code_commune is not None:
                    self.__check_commune(session, siret_entity.code_commune)

                try:
                    session.add(siret_entity)
                    session.flush()
                    logger.info(f"[SERVICE][SIRET] Siret {siret} ajouté à la base.")
                except Exception as e:
                    logger.exception(f"[SERVICE][SIRET] Error sur ajout Siret {siret}")
                    raise e

    def __check_commune(self, session: Session, code):
        instance = session.query(Commune).filter_by(code=code).one_or_none()
        if not instance:
            logger.info("[SERVICE][SIRET][IMPORT][COMMUNE] Ajout commune %s", code)
            commune = Commune(code=code)

            try:
                commune = self._maj_one_commune(commune)
            except Exception:
                logger.exception(f"[SERVICE][SIRET][IMPORT][CHORUS] Error sur ajout commune {code}")

            if commune is not None:
                session.add(commune)
                session.flush()
            instance = commune

        return instance

    def _maj_one_commune(self, commune: Commune):
        """
        Lance la MAj d'une commune
        :param commune:
        :return:
        """
        try:
            apigeo = self._api_geo.get_info_commune(commune)
            commune.label_commune = apigeo["nom"]
            if "epci" in apigeo:
                commune.code_epci = apigeo["epci"]["code"]
                commune.label_epci = apigeo["epci"]["nom"]
            if "region" in apigeo:
                commune.code_region = apigeo["region"]["code"]
                commune.label_region = apigeo["region"]["nom"]
            if "departement" in apigeo:
                commune.code_departement = apigeo["departement"]["code"]
                commune.label_departement = apigeo["departement"]["nom"]
            return commune
        except ApiGeoException:
            logger.info(f"[SERVICE][SIRET][MAJ COMMUNE] Commune {commune.code} non trouvé via API")
            return commune

    def fill_commune_info(self, session: Session, siret_entity: Siret) -> Commune | None:
        """
        Vérifie que les informations de la commune du siret sont présentes en base.
        Si elles ne sont pas présentes, les récupère via l'API geo et les ajoute en base.
        Si l'api geo ne trouve pas la commune, retourne une instance de commune avec uniquement le code rempli.
        Si aucun code commune associé au siret, renvoit None
        """
        code_commune = siret_entity.code_commune
        commune = None

        if not code_commune:
            logger.info(
                f"[SERVICE][SIRET][FILL COMMUNE] Le siret {siret_entity.code} n'a pas de code commune, on ne remplit pas les infos de la commune"
            )
        else:
            commune = self.__check_commune(session, siret_entity.code_commune)

        return commune

    def update_siret_from_api_entreprise_payload(
        self, session: Session, siret: str, etablissement: DonneesEtablissement | None, insert_only=False
    ):
        """Met à jour le siret donné depuis l'établissement qui provient de l'API entreprise

        Args:
            code (str): siret
            insert_only (bool, optional): Si mis à vrai, ne gère que l'insertion (pas d'update). Defaults to False.

        Raises:
            LimitHitError: si le ratelimiter de l'API est plein.
        """

        code = siret
        logger.info(f"[SERVICE][SIRET] Mise à jour du siret {code} avec les informations de l'API entreprise")

        siret_entity = session.query(Siret).filter_by(code=str(code)).one_or_none()
        if siret_entity is not None and insert_only:
            logger.debug(f"[SERVICE][SIRET] Le siret {code} existe déjà. On ne met pas à jour les données")
            return siret_entity
        if siret_entity is None:
            siret_entity = Siret(code=str(code))
        assert siret_entity is not None

        if etablissement is None:
            logger.warning(
                f"[SERVICE][SIRET] Aucune information sur l'entreprise via API entreprise pour le siret {code}"
            )
            return siret_entity

        self._map(siret_entity, etablissement)

        return siret_entity

    def update_siret_from_api_entreprise(self, session: Session, code: str, insert_only=False):
        """
        Comme :func:`update_siret_from_api_entreprise_payload` mais réalise l'appel à l'api entreprise.
        """
        etablissement = None
        try:
            etablissement = self._api_entreprise.donnees_etablissement(code)
        except ApiError as e:
            logger.exception(
                f"[SERVICE][SIRET] Erreur de l'api entreprise, le siret {code} ne sera pas mis à jour", exc_info=e
            )

        siret_entity = self.update_siret_from_api_entreprise_payload(session, code, etablissement, insert_only)
        return siret_entity
