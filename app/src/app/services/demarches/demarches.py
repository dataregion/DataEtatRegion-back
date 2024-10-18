import json
import logging
import string
from datetime import datetime
from pathlib import Path

from sqlalchemy import update, exc

from app import db
from app.models.demarches.demarche import Demarche
from app.models.demarches.donnee import Donnee
from app.models.demarches.dossier import Dossier
from app.services.demarches.dossiers import DossierService
from app.services.demarches.valeurs import ValeurService
from app.servicesapp.api_externes import ApisExternesService

logger = logging.getLogger(__name__)

service = ApisExternesService()


class DemarcheExistsException(Exception):
    def __init__(self):
        super().__init__("La démarche existe déjà en BDD")


def commit_session() -> None:
    """
    Commit tous les changement effectués en BDD
    :return: None
    """
    db.session.commit()


class DemarcheService:
    @staticmethod
    def exists(number: int) -> Demarche:
        """
        Vérifie si une Demarche est présente en BDD
        :param number: Numéro de la démarche à rechercher
        :return: bool
        """
        return db.session.query(Demarche.query.filter(Demarche.number == number).exists()).scalar()

    @staticmethod
    def find(number: int) -> Demarche:
        """
        Vérifie si une Demarche est présente en BDD
        :param number: Numéro de la démarche à rechercher
        :return: bool
        """
        stmt = db.select(Demarche).where(Demarche.number == number)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def save(demarche_number: int, demarche_dict: dict) -> Demarche:
        """
        Sauvegarde un objet Demarche
        :param demarche_dict:
        :param demarche_number:
        :return: Demarche
        """
        try:
            demarche_data = {
                "number": demarche_number,
                "title": demarche_dict["data"]["demarche"]["title"],
                "state": demarche_dict["data"]["demarche"]["state"],
                "centre_couts": demarche_dict["data"]["demarche"]["chorusConfiguration"]["centreDeCout"],
                "domaine_fonctionnel": demarche_dict["data"]["demarche"]["chorusConfiguration"]["domaineFonctionnel"],
                "referentiel_programmation": demarche_dict["data"]["demarche"]["chorusConfiguration"][
                    "referentielDeProgrammation"
                ],
                "date_creation": demarche_dict["data"]["demarche"]["dateCreation"],
                "date_fermeture": demarche_dict["data"]["demarche"]["dateFermeture"],
                "date_import": datetime.now(),
            }
            demarche = Demarche(**demarche_data)
            db.session.add(demarche)
            db.session.flush()
        except exc.IntegrityError:
            db.session.rollback()
            raise DemarcheExistsException()
        return demarche

    @staticmethod
    def update_reconciliation(number: int, reconciliation: dict) -> None:
        """
        Mets à jour la reconciliation d'une Demarche
        :param number: ID de la démarche
        :param reconciliation: Paramètres de la réconciliation
        :return: Demarche
        """
        stmt = update(Demarche).where(Demarche.number == number).values(reconciliation=reconciliation)
        db.session.execute(stmt)
        db.session.flush()
        db.session.commit()

    @staticmethod
    def update_affichage(number: int, affichage: dict) -> None:
        """
        Mets à jour la reconciliation d'une Demarche
        :param number: ID de la démarche
        :param affichage:
        :return: Demarche
        """
        stmt = update(Demarche).where(Demarche.number == number).values(affichage=affichage)
        db.session.execute(stmt)
        db.session.flush()
        db.session.commit()

    @staticmethod
    def delete(demarche: Demarche) -> None:
        """
        Supprime un objet Demarche
        :param demarche: Démarche à supprimer
        :return: None
        """
        db.session.delete(demarche)
        db.session.flush()
        db.session.commit()

    @staticmethod
    def integrer_demarche(demarche_number: int):
        # Vérification si la démarche existe déjà en BDD, si oui on la supprime
        demarche = DemarcheService.find(demarche_number)
        if demarche is not None:
            DemarcheService.delete(demarche)
            logging.info("[API DEMARCHES] La démarche existait déjà en BDD, maintenant supprimée pour réintégration")

        demarche_dict = DemarcheService.query_demarche(demarche_number)

        # Sauvegarde de la démarche
        demarche: Demarche = DemarcheService.save(demarche_number, demarche_dict)
        logging.info(f"[API DEMARCHES] Sauvegarde de la démarche {demarche_number}")

        # Sauvegarde des dossiers de la démarche
        DemarcheService.save_dossiers(
            demarche,
            demarche_dict["data"]["demarche"]["dossiers"]["nodes"],
            demarche_dict["data"]["demarche"]["revisions"],
        )
        logging.info("[API DEMARCHES] Sauvegarde des dossiers en BDD")
        commit_session()
        return demarche

    @staticmethod
    def query_demarche(demarche_number: int):
        # Récupération des données de la démarche via l'API Démarches Simplifiées
        query = DemarcheService.get_query_from_file("get_demarche.gql")
        demarche_dict = DemarcheService.query(query, demarche_number, None)

        page_info_dict = demarche_dict["data"]["demarche"]["dossiers"]["pageInfo"]
        while page_info_dict["hasNextPage"] is True:
            new_demarche_dict = DemarcheService.query(query, demarche_number, page_info_dict["endCursor"])
            dossiers: list[dict] = demarche_dict["data"]["demarche"]["dossiers"]["nodes"]
            dossiers += new_demarche_dict["data"]["demarche"]["dossiers"]["nodes"]
            page_info_dict = new_demarche_dict["data"]["demarche"]["dossiers"]["pageInfo"]

        logging.info("[API DEMARCHES] Récupération de la Démarche")
        return demarche_dict

    @staticmethod
    def query(query: string, demarche_number: int, after: string):
        data = {
            "operationName": "getDemarche",
            "query": query,
            "variables": {
                "demarcheNumber": demarche_number,
                "includeRevision": True,
                "after": after if after is not None else "",
            },
        }
        return service.api_demarche_simplifie.do_post(json.dumps(data))

    @staticmethod
    def save_dossiers(demarche: Demarche, dossiers_dict: list[dict], revisions_dict: list[dict]):
        # Insertion des dossiers et des valeurs des champs du dossier
        for dossier_dict in dossiers_dict:
            donnees: list[Donnee] = DossierService.get_donnees(dossier_dict, demarche.number, revisions_dict)

            # Sauvegarde du dossier
            dossier: Dossier = DossierService.save(demarche.number, dossier_dict)
            logging.info(f"[API DEMARCHES] Sauvegarde du dossier {dossier_dict['number']}")

            for champ in dossier_dict["champs"]:
                ValeurService.save(dossier.number, [d for d in donnees if d.section_name == "champ"], champ)

            for annot in dossier_dict["annotations"]:
                ValeurService.save(dossier.number, [d for d in donnees if d.section_name == "annotation"], annot)

    @staticmethod
    def get_query_from_file(query_filename: str):
        p = Path(__file__).resolve().parent / "queries" / query_filename
        with p.open("r") as f:
            query_str = f.read()
        return query_str
