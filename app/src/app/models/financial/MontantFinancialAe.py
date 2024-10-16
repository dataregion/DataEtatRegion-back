from dataclasses import dataclass

from sqlalchemy import Column, Integer, Float, ForeignKey
from app import db
from app.models.common.Audit import Audit


@dataclass
class MontantFinancialAe(Audit, db.Model):
    __tablename__ = "montant_financial_ae"
    # PK
    id: Column[int] = Column(Integer, primary_key=True)

    # FK
    id_financial_ae: Column[int] = Column(
        Integer, ForeignKey("financial_ae.id", ondelete="CASCADE"), nullable=False, index=True
    )
    montant: Column[float] = Column(Float)
    annee: Column[int] = Column(Integer, nullable=False)

    def __init__(self, montant: float, annee: int):
        self.montant = montant
        self.annee = annee
