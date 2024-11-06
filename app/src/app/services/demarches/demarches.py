import json
import logging
import string
from datetime import datetime
from pathlib import Path

from sqlalchemy import update, exc

from app import db
from app.clients.demarche_simplifie import get_or_make_api_demarche_simplifie
from app.services.demarches.dossiers import DossierService
from app.services.demarches.tokens import TokenService
from app.services.demarches.valeurs import ValeurService
from app.servicesapp.api_externes import ApisExternesService
from models.entities.demarches.Demarche import Demarche
from models.entities.demarches.Dossier import Dossier
from models.entities.demarches.ValeurDonnee import ValeurDonnee

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
    def integrer_demarche(uuid_utilisateur: string, token_id: int, demarche_number: int):
        # Vérification si la démarche existe déjà en BDD, si oui, on la supprime
        demarche = DemarcheService.find(demarche_number)
        if demarche is not None:
            DemarcheService.delete(demarche)
            logging.info("[API DEMARCHES] La démarche existait déjà en BDD, maintenant supprimée pour réintégration")

        demarche_dict = DemarcheService.query_demarche(uuid_utilisateur, token_id, demarche_number)

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
    def query_demarche(uuid_utilisateur: string, token_id: int, demarche_number: int):
        # Récupération des données de la démarche via l'API Démarches Simplifiées
        query = DemarcheService.get_query_from_file("get_demarche.gql")
        token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_id).token
        demarche_dict = DemarcheService.query(token, query, demarche_number, None)

        page_info_dict = demarche_dict["data"]["demarche"]["dossiers"]["pageInfo"]
        while page_info_dict["hasNextPage"] is True:
            new_demarche_dict = DemarcheService.query(token, query, demarche_number, page_info_dict["endCursor"])
            dossiers: list[dict] = demarche_dict["data"]["demarche"]["dossiers"]["nodes"]
            dossiers += new_demarche_dict["data"]["demarche"]["dossiers"]["nodes"]
            page_info_dict = new_demarche_dict["data"]["demarche"]["dossiers"]["pageInfo"]

        logging.info("[API DEMARCHES] Récupération de la Démarche")
        return demarche_dict

    @staticmethod
    def query(token: string, query: string, demarche_number: int, after: string):
        data = {
            "operationName": "getDemarche",
            "query": query,
            "variables": {
                "demarcheNumber": demarche_number,
                "includeRevision": True,
                "after": after if after is not None else "",
            },
        }
        return get_or_make_api_demarche_simplifie(token).do_post(json.dumps(data))

    @staticmethod
    def save_dossiers(demarche: Demarche, dossiers_dict: list[dict], revisions_dict: list[dict]):
        # Insertion des dossiers et des valeurs des champs du dossier
        dossiers: list[dict] = []
        valeurs: list[dict] = []
        for dossier_dict in dossiers_dict:
            donnees: dict = DossierService.get_donnees(dossier_dict, demarche.number, revisions_dict)

            # Sauvegarde du dossier
            dossier_dict_db: dict = DossierService.create_dossier(demarche.number, dossier_dict)
            dossiers.append(dossier_dict_db)

            for champ in dossier_dict["champs"]:
                valeurs.append(ValeurService.create_valeur_donnee(dossier_dict_db["number"], donnees, champ))

            for annot in dossier_dict["annotations"]:
                valeurs.append(ValeurService.create_valeur_donnee(dossier_dict_db["number"], donnees, annot))

        if len(dossiers) > 0:
            db.session.bulk_insert_mappings(Dossier, dossiers, render_nulls=True)

        if len(valeurs) > 0:
            db.session.bulk_insert_mappings(ValeurDonnee, valeurs, render_nulls=True)

    @staticmethod
    def get_query_from_file(query_filename: str):
        p = Path(__file__).resolve().parent / "queries" / query_filename
        with p.open("r") as f:
            query_str = f.read()
        return query_str
