from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, Date, String, Float, UniqueConstraint
from app import db
from app.models.financial import FinancialData

__all__ = ("France2030",)


@dataclass
class France2030(FinancialData, db.Model):
    __tablename__ = "france_2030"
    # PK
    id = Column(Integer, primary_key=True)

    date_dpm = Column(Date)
    operateur = Column(String(255))

    procedure = Column(String(255))
    nom_projet = Column(String)
    nom_beneficiaire = Column(String)
    typologie = Column(String)

    nom_strategie = Column(String)
    montant_subvention = Column(Float)
    montant_avance_remboursable = Column(Float)
    montant_aide = Column(Float)

    # FK
    siret = Column(String, db.ForeignKey("ref_siret.code"), nullable=True)
    code_nomenclature = Column(String, db.ForeignKey("nomenclature_france_2030.code"), nullable=True)

    # Données techniques
    file_import_taskid = Column(String(255))
    """Task ID de la tâche d'import racine pour cette ligne"""
    file_import_lineno = Column(Integer())
    """Numéro de ligne correspondant dans le fichier original"""

    __table_args__ = (
        UniqueConstraint("file_import_taskid", "file_import_lineno", name="uq_file_line_import_france_2030"),
    )

    def __init__(self, **kwargs):
        """
        init à partir d'une ligne issue d'un fichier
        """
        self.update_attribute(kwargs)

    def __setattr__(self, key, value):
        if key == "date_dpm" and isinstance(value, int):
            value = datetime.fromtimestamp(value / 1000)

        super().__setattr__(key, value)

    @staticmethod
    def get_columns_files():
        return [
            "date_dpm",
            "operateur",
            "procedure",
            "nom_projet",
            "nom_beneficiaire",
            "siret",
            "typologie",
            "regions",
            "localisation_geo",
            "acteur_emergent",
            "nom_strategie",
            "code_nomenclature",
            "nomemclature",
            "montant_subvention",
            "montant_avance_remboursable",
            "montant_aide",
        ]
