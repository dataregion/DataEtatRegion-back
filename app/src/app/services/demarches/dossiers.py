import logging

from app import db
from app.services.demarches.donnees import DonneeService
from models.entities.demarches.Dossier import Dossier
from models.entities.demarches.Reconciliation import Reconciliation


class DossierService:
    @staticmethod
    def find_by_number(number: int) -> Dossier:
        stmt = db.select(Dossier).where(Dossier.number == number)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_by_demarche(demarche_number: int, statut: str) -> list[Dossier]:
        stmt = db.select(Dossier).where(Dossier.demarche_number == demarche_number, Dossier.state == statut)
        return db.session.execute(stmt).all()

    @staticmethod
    def find_by_financial_ae_id(financial_ae_id) -> Dossier:
        stmt = (
            db.select(Dossier)
            .join(Reconciliation, Dossier.number == Reconciliation.dossier_number)
            .where(Reconciliation.financial_ae_id == financial_ae_id)
        )
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_donnees(dossier_dict: dict, demarche_number: int, revisions: list[dict]):
        donnees: dict = dict()
        revision = next(r for r in revisions if r["id"] == dossier_dict["demarche"]["revision"]["id"])

        # Récupération des champs et des annotations en amont de l'insert des dossiers
        for champ in revision["champDescriptors"]:
            donnee = DonneeService.get_or_create(champ, "champ", demarche_number)
            donnees[donnee.id_ds] = donnee
        for annotation in revision["annotationDescriptors"]:
            donnee = DonneeService.get_or_create(annotation, "annotation", demarche_number)
            donnees[donnee.id_ds] = donnee

        logging.info(f"[API DEMARCHES] Récupération des champs du dossier {dossier_dict['number']}")
        return donnees

    @staticmethod
    def create_dossier(demarche_number: int, dossier_dict: dict) -> dict:
        """
        Sauvegarde un objet Dossier
        :param dossier_dict:
        :param demarche_number:
        :return: Dossier
        """
        return {
            "number": dossier_dict["number"],
            "demarche_number": demarche_number,
            "revision_id": dossier_dict["demarche"]["revision"]["id"],
            "state": dossier_dict["state"],
            "siret": dossier_dict["demandeur"]["siret"] if "siret" in dossier_dict["demandeur"] else None,
            "date_depot": dossier_dict["dateDepot"],
            "date_derniere_modification": dossier_dict["dateDerniereModification"],
        }
