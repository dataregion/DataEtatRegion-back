import logging

from app import db
from app.models.demarches.dossier import Dossier
from app.models.demarches.donnee import Donnee

from app.services.demarches.donnees import DonneeService


class DossierService:
    @staticmethod
    def find_by_demarche(demarche_number: int, statut: str) -> list[Dossier]:
        stmt = db.select(Dossier).where(Dossier.demarche_number == demarche_number, Dossier.state == statut)
        return db.session.execute(stmt).scalars()

    @staticmethod
    def get_donnees(dossier_dict: dict, demarche_number: str, revisions: list[dict]):
        donnees: dict[Donnee] = []
        revision = next(r for r in revisions if r["id"] == dossier_dict["demarche"]["revision"]["id"])

        # Récupération des champs et des annotations en amont de l'insert des dossiers
        for champ in revision["champDescriptors"]:
            donnees.append(DonneeService.get_or_create(champ, "champ", demarche_number))
        for annotation in revision["annotationDescriptors"]:
            donnees.append(DonneeService.get_or_create(annotation, "annotation", demarche_number))
        logging.info(f"[API DEMARCHES] Récupération des champs du dossier {dossier_dict['number']}")
        return donnees

    @staticmethod
    def save(demarche_number: str, dossier_dict: dict) -> Dossier:
        """
        Sauvegarde un objet Dossier
        :param dossier: Objet à sauvegarder
        :return: Dossier
        """
        dossier_data = {
            "number": dossier_dict["number"],
            "demarche_number": demarche_number,
            "revision_id": dossier_dict["demarche"]["revision"]["id"],
            "state": dossier_dict["state"],
            "siret": dossier_dict["demandeur"]["siret"] if "siret" in dossier_dict["demandeur"] else None,
            "date_depot": dossier_dict["dateDepot"],
            "date_derniere_modification": dossier_dict["dateDerniereModification"],
        }
        dossier: Dossier = Dossier(**dossier_data)
        db.session.add(dossier)
        db.session.flush()
        return dossier
