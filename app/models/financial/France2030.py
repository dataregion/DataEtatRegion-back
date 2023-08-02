from dataclasses import dataclass

from sqlalchemy import Column, Integer, Date, String, Float
from app import db
from app.models.financial import FinancialData

__all__ = ('France2030',)

@dataclass
class France2030(FinancialData, db.Model):
    __tablename__ = 'france_2030'
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
    montant_aide= Column(Float)

    # FK
    siret = Column(String, db.ForeignKey('ref_siret.code'), nullable=True)
    code_nomenclature = Column(String, db.ForeignKey('nomenclature_france_2030.code'), nullable=True)

    @staticmethod
    def get_columns_files():
        return ['date_dpm', 'operateur', 'procedure',
                'nom_projet', 'nom_beneficiaire', 'siret', 'typologie',
                'regions', 'localisation_geo', 'acteur_emergent', 'nom_strategie',
                'code_nomenclature', 'nomemclature', 'montant_subvention',
                'montant_avance_remboursable', 'montant_aide']


