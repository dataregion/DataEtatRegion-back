from datetime import datetime
import logging

from app import db
from app.models.demarches.demarche import Demarche
from sqlalchemy import update


logger = logging.getLogger(__name__)


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
    def save(demarche_number: str, demarche_dict: dict) -> Demarche:
        """
        Sauvegarde un objet Demarche
        :param demarche: Objet à sauvegarder
        :return: Demarche
        """
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
            "date_import": datetime.now()
        }
        demarche: Demarche = Demarche(**demarche_data)
        db.session.add(demarche)
        db.session.flush()
        return demarche


    @staticmethod
    def update_reconciliation(number: int, reconciliation: dict) -> None:
        """
        Mets à jour la reconciliation d'une Demarche
        :param number: ID de la démarche
        :param reconciliation: Paramètres de la réconciliation
        :return: Demarche
        """
        stmt = (
            update(Demarche)
            .where(Demarche.number == number)
            .values(reconciliation=reconciliation)
        )
        demarche = db.session.execute(stmt)
        db.session.flush()
        db.session.commit()


    @staticmethod
    def update_affichage(number: int, affichage: dict) -> None:
        """
        Mets à jour la reconciliation d'une Demarche
        :param number: ID de la démarche
        :param reconciliation: Paramètres de la réconciliation
        :return: Demarche
        """
        stmt = (
            update(Demarche)
            .where(Demarche.number == number)
            .values(affichage=affichage)
        )
        db.session.execute(stmt)
        db.session.flush()
        db.session.commit()


    @staticmethod
    def delete(demarche: Demarche) -> None:
        """
        Supprime un objet Demarche
        :param Demarche: Démarche à supprimer
        :return: None
        """
        db.session.delete(demarche)
        db.session.flush()
        db.session.commit()


