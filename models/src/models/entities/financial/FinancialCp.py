from datetime import datetime
from dataclasses import dataclass

import pandas as pd
from models import _PersistenceBaseModelInstance
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer,
    DateTime,
    Float,
    UniqueConstraint,
)
from models.entities.financial.FinancialData import FinancialData
from models.entities.refs.Region import get_code_region_by_code_comp


@dataclass
class FinancialCp(FinancialData, _PersistenceBaseModelInstance()):
    __tablename__ = "financial_cp"

    # numero de la dépense (non unique).
    n_dp: Column[str] = Column(String, nullable=False)

    # FK AE
    id_ae: Column[int] = Column(
        Integer,
        ForeignKey("financial_ae.id", ondelete="cascade"),
        nullable=True,
        index=True,
    )

    # liens vers les AE
    n_ej: Column[str] = Column(String, nullable=True)
    n_poste_ej: int = Column(Integer, nullable=True)
    data_source = Column(String, nullable=False)

    # FK
    source_region: Column[str] = Column(
        String, ForeignKey("ref_region.code"), nullable=False
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
    siret: Column[str] = Column(String, ForeignKey("ref_siret.code"), nullable=True)
    groupe_marchandise: Column[str] = Column(
        String, ForeignKey("ref_groupe_marchandise.code"), nullable=True
    )
    localisation_interministerielle: str = Column(
        String, ForeignKey("ref_localisation_interministerielle.code"), nullable=False
    )
    fournisseur_paye: Column[str] = Column(
        String, ForeignKey("ref_fournisseur_titulaire.code"), nullable=False
    )

    # Autre colonne
    date_base_dp: datetime = Column(DateTime, nullable=True)
    date_derniere_operation_dp: datetime = Column(DateTime, nullable=True)

    compte_budgetaire: Column[str] = Column(String(255), nullable=True)
    contrat_etat_region: Column[str] = Column(String(255), nullable=True)
    montant: float = Column(Float)
    annee: int = Column(Integer, nullable=False)

    #ajout donnée issue de AIFE (ces trois colonnes avec le champ n_dp composent la clé unique d'une Dépense)
    societe: Column[str] = Column(String,nullable=True)
    exercice_comptable: Column[str] = Column(String,nullable=True)
    n_poste_dp: Column[str] = Column(String, nullable=True)

    #ajout autre colonne AIFE
    tranche_fonctionnelle: Column[str] = Column(String,nullable=True)
    fonds: Column[str] = Column(String,nullable=True)
    projet_analytique: Column[str] = Column(String,nullable=True)
    type_piece: Column[str] = Column(String,nullable=True)


    # Données techniques

    file_import_taskid = Column(String(255))
    """Task ID de la tâche d'import racine pour cette ligne"""
    file_import_lineno = Column(Integer())
    """Numéro de ligne correspondant dans le fichier original"""

    __table_args__ = (
        UniqueConstraint(
            "file_import_taskid", "file_import_lineno", name="uq_file_line_import_cp"
        ),
    )

    def __init__(self, line_chorus: dict, source_region: str, annee: int):
        """
        init à partir d'une ligne issue d'un fichier chorus

        :param line_chorus: dict contenant les valeurs d'une ligne issue d'un fichier chorus
        :param source_region:
        :param annee:
        """
        
        self.update_attribute(line_chorus)

        if source_region is not None :
            self.source_region = source_region
        else :
            self.source_region = get_code_region_by_code_comp(self.societe)
        self.annee = annee


    def should_update(self, new_financial: dict) -> bool:
        return True

    def __setattr__(self, key, value):
        if (key == "n_ej" or key == "n_poste_ej") and value == "#":
            value = None

        elif (
            key == "date_base_dp" or key == "date_derniere_operation_dp"
        ) and isinstance(value, str):
            if value in ("#", ""):
                value = None
            else:
                value = datetime.strptime(value.replace("/","."), "%d.%m.%Y")

        super().__setattr__(key, value)

    @staticmethod
    def get_columns_files_cp():
        return [
            "programme",
            "domaine_fonctionnel",
            "centre_couts",
            "referentiel_programmation",
            "n_ej",
            "n_poste_ej",
            "n_dp",
            "date_base_dp",
            "date_derniere_operation_dp",
            "n_sf",
            "data_sf",
            "fournisseur_paye",
            "fournisseur_paye_label",
            "siret",
            "compte_code",
            "compte_budgetaire",
            "groupe_marchandise",
            "contrat_etat_region",
            "contrat_etat_region_2",
            "localisation_interministerielle",
            "montant",
        ]

    @staticmethod
    def get_columns_fichier_nat_cp():
        return [
            "programme",
            "domaine_fonctionnel",
            "centre_couts",
            "referentiel_programmation",
            "n_ej",
            "n_poste_ej",
            "n_dp",
            "date_base_dp",
            "date_derniere_operation_dp",
            "fournisseur_paye",
            "fournisseur_paye_label",
            "siret",
            "compte_code",
            "compte_budgetaire",
            "groupe_marchandise",
            "contrat_etat_region",
            "localisation_interministerielle",
            "montant",
            "exercice_comptable",
            "n_poste_dp",
            "programme_doublon",
            "tranche_fonctionnelle",
            "fonds",
            "projet_analytique",
            "societe",
            "type_piece"
        ]

    @staticmethod
    def get_columns_types_fichier_nat_cp():
        return {
            "programme": str,
            "domaine_fonctionnel": str,
            "centre_couts": str,
            "referentiel_programmation": str,
            "n_ej": str,
            "n_poste_ej": str,
            "n_dp": str,
            "date_base_dp": str,
            "date_derniere_operation_dp": str,
            "fournisseur_paye": str,
            "fournisseur_paye_label": str,
            "siret": str,
            "compte_code": str,
            "compte_budgetaire": str,
            "groupe_marchandise": str,
            "contrat_etat_region": str,
            "localisation_interministerielle": str,
            "montant": str,
            "exercice_comptable": str,
            "n_poste_dp": str,
            "programme_doublon": str,
            "tranche_fonctionnelle": str,
            "fonds": str,
            "projet_analytique": str,
            "societe": str,
            "type_piece": str
        }

def _convert_date_format(date_str):
    if pd.isna(date_str):  # Gérer les NaN (y compris sous forme de float)
        return None
    try:
        date_obj = datetime.strptime(str(date_str), "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return None
