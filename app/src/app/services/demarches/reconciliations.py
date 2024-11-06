import logging
import re
import string
from datetime import datetime

from sqlalchemy import delete, and_
from sqlalchemy.exc import IntegrityError

from app import db
from app.services import BuilderStatementFinancial
from app.services.demarches.demarches import DemarcheService
from app.services.demarches.dossiers import DossierService
from app.services.demarches.valeurs import ValeurService
from app.services.tags import ApplyTagForAutomation, select_tag
from models.entities.common.Tags import TagAssociation
from models.entities.demarches.Dossier import Dossier
from models.entities.demarches.Reconciliation import Reconciliation
from models.entities.financial.FinancialAe import FinancialAe
from models.value_objects import TagVO

logger = logging.getLogger(__name__)


class ReconciliationService:
    @staticmethod
    def find_by_demarche_number(demarche_number: int) -> list[Reconciliation]:
        stmt = (
            db.select(Reconciliation)
            .join(Dossier, Dossier.number == Reconciliation.dossier_number)
            .where(Dossier.demarche_number == demarche_number)
        )
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def save(reconciliation: Reconciliation) -> Reconciliation:
        """
        Sauvegarde un objet Demarche
        :param reconciliation: Objet à sauvegarder
        :return: Reconciliation
        """
        db.session.add(reconciliation)
        db.session.flush()
        return reconciliation

    @staticmethod
    def clear_reconciliations(demarche_number: int):
        reconciliations = ReconciliationService.find_by_demarche_number(demarche_number)
        ReconciliationService.clear_previous_tags_reconcilie_ds(reconciliations)

        id_reconciliations = [reconciliation.id for reconciliation in reconciliations]
        db.session.execute(delete(Reconciliation).where(Reconciliation.id.in_(id_reconciliations)))
        db.session.commit()

    @staticmethod
    def do_reconciliation(demarche_number: int, champs_reconciliation: dict, cadre: dict):
        """
        Effectue la réconciliation entre les dossiers de la démarche et les lignes chorus
        :param: Numéro de la démarche
        :param: Paramètres pour la reconciliation
        """
        ReconciliationService.clear_reconciliations(demarche_number)

        DemarcheService.update_reconciliation(demarche_number, champs_reconciliation)

        dossiers = DossierService.find_by_demarche(demarche_number, "accepte")
        date_reconciliation = datetime.now()
        reconciliations = []
        for dossier_row in dossiers:
            dossier = dossier_row[0]
            valeurs = ValeurService.get_dict_valeurs(dossier.number, champs_reconciliation)

            ligne_chorus = ReconciliationService.get_ligne_chorus_par_type_reconciliation(
                dossier, champs_reconciliation, valeurs, cadre
            )

            if ligne_chorus is not None:
                reconciliation = Reconciliation(
                    dossier_number=dossier.number,
                    financial_ae_id=ligne_chorus.id,
                    date_reconciliation=date_reconciliation,
                )
                try:
                    ReconciliationService.save(reconciliation)
                    reconciliations.append(reconciliation)
                except IntegrityError as e:
                    db.session.rollback()
                    logger.error(
                        f"Erreur lors de la réconciliation entre le dossier {dossier.number} et la ligne financière {ligne_chorus.id}. La ligne a peut-être déjà été réconciliée avec un autre dossier")
        ReconciliationService.add_tag_reconcilie_ds(reconciliations)
        db.session.commit()
        return reconciliations

    @staticmethod
    def get_ligne_chorus_par_type_reconciliation(
            dossier: Dossier, champs_reconciliation: dict, valeurs: dict, cadre: dict
    ):
        lignes = []
        if "champEJ" in champs_reconciliation:
            if champs_reconciliation["champEJ"] in valeurs:
                valeur_champ_ej = valeurs[champs_reconciliation["champEJ"]]
                lignes = ReconciliationService.get_lignes_chorus_num_ej(valeur_champ_ej)
        elif "champMontant" in champs_reconciliation:
            if champs_reconciliation["champMontant"] in valeurs:
                valeur_champ_montant = ReconciliationService.convert_valeur_to_float(
                    valeurs[champs_reconciliation["champMontant"]]
                )
                if valeur_champ_montant is not None and valeur_champ_montant != "":
                    lignes = ReconciliationService.get_lignes_chorus_siret_montant(
                        dossier.siret, valeur_champ_montant, cadre
                    )
        else:
            # TODO Implémenter les méthodes de réconciliation manquantes
            logger.info("Méthode de réconciliation non implémentée")
        # On ne réconcilie pas si on a plusieurs résultats
        if len(lignes) != 1:
            return None
        return lignes[0]

    @staticmethod
    def convert_valeur_to_float(valeur: string):
        valeur = re.sub(
            r"[^0-9.,]", "", valeur.replace(",", ".")
        )  # On adapte la valeur si besoin pour la convertir en float
        try:
            return float(valeur)
        except ValueError:
            return None

    @staticmethod
    def get_lignes_chorus_num_ej(num_ej: string):
        return BuilderStatementFinancial().select_ae().where_n_ej(num_ej).do_all().all()

    @staticmethod
    def get_lignes_chorus_siret_montant(siret: string, montant: float, cadre: dict):
        lignes = (
            BuilderStatementFinancial()
            .select_ae()
            .join_montant()
            .where_siret(siret)
            .where_montant(montant)
            .do_all()
            .all()
        )
        lignes = list(
            filter(
                lambda ligne: ReconciliationService.filter_lignes_chorus_par_param_reconciliation(ligne, cadre), lignes
            )
        )
        return lignes

    @staticmethod
    def filter_lignes_chorus_par_param_reconciliation(financial_ae: FinancialAe, cadre: dict):
        centre_couts = cadre.get("centreCouts")
        match_centre_couts = centre_couts is None or financial_ae.centre_couts == centre_couts

        domaine_fonctionnel = cadre.get("domaineFonctionnel")
        match_domaine_fonctionnel = (
                domaine_fonctionnel is None or financial_ae.domaine_fonctionnel == domaine_fonctionnel
        )

        ref_prog = cadre.get("refProg")
        match_ref_prog = ref_prog is None or financial_ae.referentiel_programmation == ref_prog

        annee = cadre.get("annee")
        match_annee = annee is None or financial_ae.annee == annee

        commune_db = financial_ae.ref_siret.ref_commune

        commune = cadre.get("commune")
        match_commune = commune is None or commune_db.code == commune

        epci = cadre.get("epci")
        match_epci = epci is None or commune_db.code_epci == epci

        departement = cadre.get("departement")
        match_departement = departement is None or commune_db.code_departement == departement

        region = cadre.get("region")
        match_region = region is None or commune_db.code_region == region

        return (
                match_centre_couts
                and match_domaine_fonctionnel
                and match_ref_prog
                and match_annee
                and match_commune
                and match_epci
                and match_departement
                and match_region
        )

    @staticmethod
    def add_tag_reconcilie_ds(reconciliations: list[Reconciliation]):
        id_lignes = [reconciliation.financial_ae_id for reconciliation in reconciliations]
        where_clause = FinancialAe.id.in_(id_lignes)
        apply_task = ApplyTagForAutomation(select_tag(TagVO(type="reconcilie-ds", value=None)))
        apply_task.apply_tags_ae(where_clause)

    @staticmethod
    def clear_previous_tags_reconcilie_ds(reconciliations: list[Reconciliation]):
        tag = select_tag(TagVO(type="reconcilie-ds", value=None))
        id_lignes = [reconciliation.financial_ae_id for reconciliation in reconciliations]
        where_clause = and_(TagAssociation.tag_id == tag.id, TagAssociation.financial_ae.in_(id_lignes))
        db.session.execute(delete(TagAssociation).where(where_clause))
