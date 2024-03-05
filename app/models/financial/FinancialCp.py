from datetime import datetime
from dataclasses import dataclass

from marshmallow import fields
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Float, UniqueConstraint
from app import db, ma
from app.models.financial import FinancialData


@dataclass
class FinancialCp(FinancialData, db.Model):
    __tablename__ = "financial_cp"

    # numero de la dépense (non unique).
    n_dp: Column[str] = Column(String, nullable=False)

    # FK AE
    id_ae: int = Column(Integer, ForeignKey("financial_ae.id", ondelete="cascade"), nullable=True, index=True)

    # liens vers les AE
    n_ej: Column[str] = Column(String, nullable=True)
    n_poste_ej: int = Column(Integer, nullable=True)

    # FK
    source_region: Column[str] = Column(String, ForeignKey("ref_region.code"), nullable=False)
    programme: Column[str] = Column(String, ForeignKey("ref_code_programme.code"), nullable=False)
    domaine_fonctionnel: Column[str] = Column(String, db.ForeignKey("ref_domaine_fonctionnel.code"), nullable=False)
    centre_couts: Column[str] = Column(String, db.ForeignKey("ref_centre_couts.code"), nullable=False)
    referentiel_programmation: Column[str] = Column(String, db.ForeignKey("ref_programmation.code"), nullable=False)
    siret: Column[str] = Column(String, db.ForeignKey("ref_siret.code"), nullable=True)
    groupe_marchandise: Column[str] = Column(String, db.ForeignKey("ref_groupe_marchandise.code"), nullable=False)
    localisation_interministerielle: str = Column(
        String, db.ForeignKey("ref_localisation_interministerielle.code"), nullable=False
    )
    fournisseur_paye: Column[str] = Column(String, db.ForeignKey("ref_fournisseur_titulaire.code"), nullable=False)

    # Autre colonne
    date_base_dp: datetime = Column(DateTime, nullable=True)
    date_derniere_operation_dp: datetime = Column(DateTime, nullable=True)

    compte_budgetaire: Column[str] = Column(String(255), nullable=True)
    contrat_etat_region: Column[str] = Column(String(255), nullable=True)
    montant: float = Column(Float)
    annee: int = Column(Integer, nullable=False)

    # Données techniques

    file_import_taskid = Column(String(255))
    """Task ID de la tâche d'import racine pour cette ligne"""
    file_import_lineno = Column(Integer())
    """Numéro de ligne correspondant dans le fichier original"""

    __table_args__ = (UniqueConstraint("file_import_taskid", "file_import_lineno", name="uq_file_line_import_cp"),)

    def __init__(self, line_chorus: dict, source_region: str, annee: int):
        """
        init à partir d'une ligne issue d'un fichier chorus

        :param line_chorus: dict contenant les valeurs d'une ligne issue d'un fichier chorus
        :param source_region:
        :param annee:
        """

        self.source_region = source_region
        self.annee = annee

        self.update_attribute(line_chorus)

    def should_update(self, new_financial: dict) -> bool:
        return True

    def __setattr__(self, key, value):
        if (key == "n_ej" or key == "n_poste_ej") and value == "#":
            value = None

        if (key == "date_base_dp" or key == "date_derniere_operation_dp") and isinstance(value, str):
            if value == "#":
                value = None
            else:
                value = datetime.strptime(value, "%d.%m.%Y")

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


class FinancialCpSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FinancialCp
        exclude = (
            "id",
            "id_ae",
            "n_ej",
            "n_poste_ej",
            "annee",
            "compte_budgetaire",
            "contrat_etat_region",
            "date_derniere_operation_dp",
            "file_import_lineno",
            "file_import_taskid",
            "updated_at",
            "created_at",
        )

    n_dp = fields.String()
    montant = fields.Float()
    date_base_dp = fields.String()
