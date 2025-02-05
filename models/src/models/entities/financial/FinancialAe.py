import logging
from datetime import datetime
from dataclasses import dataclass

from models import _PersistenceBaseModelInstance
from models.entities.common.Tags import Tags
from models.entities.financial.FinancialData import FinancialData
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped

from models.entities.financial.FinancialCp import FinancialCp  # noqa: F401
from models.entities.financial.MontantFinancialAe import MontantFinancialAe
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.DomaineFonctionnel import DomaineFonctionnel
from models.entities.refs.GroupeMarchandise import GroupeMarchandise
from models.entities.refs.LocalisationInterministerielle import (
    LocalisationInterministerielle,
)
from models.entities.refs.ReferentielProgrammation import ReferentielProgrammation
from models.entities.refs.Region import get_code_region_by_code_comp
from models.entities.refs.Siret import Siret


COLUMN_MONTANT_NAME = "montant"

__all__ = ("FinancialAe",)


@dataclass
class FinancialAe(FinancialData, _PersistenceBaseModelInstance()):
    __tablename__ = "financial_ae"
    __table_args__ = (
        UniqueConstraint(
            "n_ej", "n_poste_ej", "data_source", name="unique_ej_poste_ej_data_source"
        ),
    )

    # UNIQUE
    n_ej: Column[str] = Column(String, nullable=False)
    n_poste_ej: Column[int] = Column(Integer, nullable=False)
    data_source = Column(String, nullable=False)

    # liens vers les référentiels
    source_region: Column[str] = Column(
        String, ForeignKey("ref_region.code"), nullable=True
    )
    programme: Column[str] = Column(
        String, ForeignKey("ref_code_programme.code"), nullable=False
    )
    domaine_fonctionnel: Column[str] = Column(
        String, ForeignKey("ref_domaine_fonctionnel.code"), nullable=False
    )
    centre_couts: Column[str] = Column(
        String, ForeignKey("ref_centre_couts.code"), nullable=False
    )
    referentiel_programmation: Column[str] = Column(
        String, ForeignKey("ref_programmation.code"), nullable=False
    )
    localisation_interministerielle: Column[str] = Column(
        String, ForeignKey("ref_localisation_interministerielle.code"), nullable=False
    )
    groupe_marchandise: Column[str] = Column(
        String, ForeignKey("ref_groupe_marchandise.code"), nullable=False
    )
    fournisseur_titulaire: Column[str] = Column(
        String, ForeignKey("ref_fournisseur_titulaire.code"), nullable=True
    )
    siret: Column[str] = Column(String, ForeignKey("ref_siret.code"), nullable=True)

    # autre colonnes
    date_modification_ej: Column[datetime] = Column(
        DateTime, nullable=True
    )  # date issue du fichier Chorus
    date_replication: Column[datetime] = Column(
        DateTime, nullable=True
    )  # Date de création de l'EJ
    compte_budgetaire: Column[str] = Column(String(255), nullable=False)
    contrat_etat_region: Column[str] = Column(String(255))
    annee: Column[int] = Column(Integer, nullable=False)  # annee de l'AE chorus

    #Ajout colonne AIFE
    tranche_fonctionnelle: Column[str] = Column(String,nullable=True)
    fonds: Column[str] = Column(String,nullable=True)
    projet_analytique: Column[str] = Column(String,nullable=True)
    axe_ministeriel_1: Column[str] = Column(String,nullable=True)
    axe_ministeriel_2: Column[str] = Column(String,nullable=True)
    societe: Column[str] = Column(String,nullable=True)
    centre_financier: Column[str] = Column(String,nullable=True)


    tags: Mapped[Tags] = relationship(
        "Tags", uselist=True, lazy="select", secondary="tag_association", viewonly=True
    )
    montant_ae = relationship("MontantFinancialAe", uselist=True, lazy="select")
    financial_cp = relationship("FinancialCp", uselist=True, lazy="select")
    ref_programme: Mapped[CodeProgramme] = relationship("CodeProgramme", lazy="select")
    ref_domaine_fonctionnel: Mapped[DomaineFonctionnel] = relationship(
        "DomaineFonctionnel", lazy="select"
    )
    ref_groupe_marchandise: Mapped[GroupeMarchandise] = relationship(
        "GroupeMarchandise", lazy="select"
    )
    ref_ref_programmation: Mapped[ReferentielProgrammation] = relationship(
        "ReferentielProgrammation", lazy="select"
    )
    ref_siret: Mapped[Siret] = relationship("Siret", lazy="select")
    ref_localisation_interministerielle: Mapped[LocalisationInterministerielle] = (
        relationship("LocalisationInterministerielle", lazy="select")
    )

    @hybrid_property
    def montant_ae_total(self):
        return sum(
            montant_financial_ae.montant for montant_financial_ae in self.montant_ae
        )

    @hybrid_property
    def montant_cp(self):
        return sum(financial_cp.montant for financial_cp in self.financial_cp)

    @hybrid_property
    def date_cp(self):
        if self.financial_cp:
            return max(
                self.financial_cp, key=lambda obj: obj.date_derniere_operation_dp
            ).date_derniere_operation_dp
        return None

    def __init__(self, **kwargs):
        """
        init à partir d'une ligne issue d'un fichier chorus
        """
        self.update_attribute(kwargs)

    def __setattr__(self, key, value):
        if (key == "date_modification_ej" or key == "date_replication") and isinstance(
            value, str
        ):
            value = datetime.strptime(value, "%d.%m.%Y")

        super().__setattr__(key, value)

    def update_attribute(self, new_financial: dict):
        # Applicatin montant négatif
        if self._should_update_montant_ae(new_financial):
            nouveau_montant = (
                float(new_financial[COLUMN_MONTANT_NAME].replace(",", "."))
                if isinstance(new_financial[COLUMN_MONTANT_NAME], str)
                else new_financial[COLUMN_MONTANT_NAME]
            )
            self.add_or_update_montant_ae(
                nouveau_montant, new_financial[FinancialAe.annee.key]
            )
            if nouveau_montant < 0 and self.annee:
                del new_financial[
                    FinancialAe.annee.key
                ]  # on ne maj pas l'année comptable si montant <0

        super().update_attribute(new_financial)

    def should_update(self, new_financial: dict) -> bool:
        """
        Indique si MAJ ou non l'objet
        :param new_financial:
        :return:
        """

        if self._should_update_montant_ae(new_financial):
            logging.debug(
                f"[FINANCIAL AE] Montant negatif détecté, application sur ancien montant {self.n_poste_ej}, {self.n_ej}"
            )
            return True
        else:
            return (
                datetime.strptime(new_financial["date_modification_ej"], "%d.%m.%Y")
                > self.date_modification_ej
            )

    def add_or_update_montant_ae(self, nouveau_montant: float, annee):
        """
        Ajoute un montant à une ligne AE
        :param nouveau_montant: le nouveau montant à ajouter
        :param annee: l'année comptable
        :return:
        """
        if (
            self.montant_ae is None or not self.montant_ae
        ):  # si aucun montant AE encore, on ajoute
            self.montant_ae = [MontantFinancialAe(montant=nouveau_montant, annee=annee)]
        else:
            montant_ae_annee = next(
                (
                    montant_ae
                    for montant_ae in self.montant_ae
                    if montant_ae.annee == annee
                ),
                None,
            )  # recherche d'un montant sur la même année existant

            if nouveau_montant > 0:  # Si nouveau montant positif
                montant_ae_positif = next(
                    (
                        montant_ae
                        for montant_ae in self.montant_ae
                        if montant_ae.montant > 0
                    ),
                    None,
                )

                if montant_ae_positif is None:
                    if (
                        montant_ae_annee is None
                    ):  # si aucun montant positif enregistré et sur, alors on ajoute
                        self.montant_ae.append(
                            MontantFinancialAe(montant=nouveau_montant, annee=annee)
                        )
                    else:
                        montant_ae_annee.montant = nouveau_montant
                        montant_ae_annee.annee = annee
                else:
                    # sinon je prend le montant positif le plus récent
                    montant_ae_positif.montant = (
                        nouveau_montant
                        if (montant_ae_positif.annee <= annee)
                        else montant_ae_positif.montant
                    )
                    montant_ae_positif.annee = (
                        annee
                        if (montant_ae_positif.annee <= annee)
                        else montant_ae_positif.annee
                    )

            else:  # nouveau_montant < 0
                if (
                    montant_ae_annee is None
                ):  # si l'année n'est pas déjà enregistré, alors on ajoute le montant
                    self.montant_ae.append(
                        MontantFinancialAe(montant=nouveau_montant, annee=annee)
                    )
                else:  # sinon on MAJ
                    montant_ae_annee.montant = nouveau_montant

    def _should_update_montant_ae(self, new_financial: dict) -> bool:
        """
        ajoute ou maj un montant dans montant_ae
        :param new_financial:
        :return:
        """
        if (
            self.source_region is not None
            and new_financial[FinancialAe.source_region.key] != self.source_region
        ):
            return False

        if COLUMN_MONTANT_NAME not in new_financial:
            return False

        nouveau_montant = (
            float(new_financial[COLUMN_MONTANT_NAME].replace(",", "."))
            if isinstance(new_financial[COLUMN_MONTANT_NAME], str)
            else new_financial[COLUMN_MONTANT_NAME]
        )

        annee = new_financial[FinancialAe.annee.key]

        if any(
            montant_ae.montant == nouveau_montant and montant_ae.annee == annee
            for montant_ae in self.montant_ae
        ):
            return False

        return True

    @staticmethod
    def get_columns_files_ae():
        return [
            "programme",
            "domaine_fonctionnel",
            "centre_couts",
            "referentiel_programmation",
            COLUMN_NEJ_NAME,
            "date_replication",
            "n_poste_ej",
            "date_modification_ej",
            "fournisseur_titulaire",
            "fournisseur_label",
            "siret",
            "compte_code",
            "compte_budgetaire",
            "groupe_marchandise",
            "contrat_etat_region",
            "contrat_etat_region_2",
            "localisation_interministerielle",
            COLUMN_MONTANT_NAME,
        ]

    @staticmethod
    def get_columns_fichier_nat_ae():
        return [
            "programme",
            "domaine_fonctionnel",
            "centre_couts",
            "referentiel_programmation",
            COLUMN_NEJ_NAME,
            "date_replication",
            "n_poste_ej",
            "date_modification_ej",
            "fournisseur_titulaire",
            "fournisseur_titulaire_label",
            "siret",
            "compte_code",
            "compte_budgetaire",
            "groupe_marchandise",
            "contrat_etat_region",
            "localisation_interministerielle",
            COLUMN_MONTANT_NAME,
            "centre_financier",
            "tranche_fonctionnelle",
            "axe_ministeriel_1",
            "fonds",
            "projet_analytique",
            "axe_ministeriel_2",
            "societe"
        ]

    @staticmethod
    def get_columns_type_fichier_nat_ae():
        return {
            "programme": str,
            "domaine_fonctionnel": str,
            "centre_couts": str,
            "referentiel_programmation": str,
            COLUMN_NEJ_NAME: str,
            "date_replication": str,
            "n_poste_ej": str,
            "date_modification_ej": str,
            "fournisseur_titulaire": str,
            "fournisseur_titulaire_label": str,
            "siret": str,
            "compte_code": str,
            "compte_budgetaire": str,
            "groupe_marchandise": str,
            "contrat_etat_region": str,
            "localisation_interministerielle": str,
            COLUMN_MONTANT_NAME: str,
            "centre_financier": str,
            "tranche_fonctionnelle": str,
            "axe_ministeriel_1": str,
            "fonds": str,
            "projet_analytique": str,
            "axe_ministeriel_2": str,
            "societe": str
        }

    def _serialize(self, code: String, attr, obj: "FinancialAe", **kwargs):
        if code is None:
            return {}
        return {
            "nom_beneficiare": obj.ref_siret.denomination,
            "code": code,
            "categorie_juridique": obj.ref_siret.type_categorie_juridique,
            "qpv": (
                {
                    "code": obj.ref_siret.ref_qpv.code,
                    "label": obj.ref_siret.ref_qpv.label,
                }
                if obj.ref_siret.ref_qpv is not None
                else None
            ),
        }


COLUMN_NEJ_NAME = "n_ej"
