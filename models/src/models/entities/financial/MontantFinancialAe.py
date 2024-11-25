from dataclasses import dataclass

from models import _PersistenceBaseModelInstance
from sqlalchemy import Column, Integer, Float, ForeignKey
from models.entities.common.Audit import _Audit


@dataclass
class MontantFinancialAe(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "montant_financial_ae"
    # PK
    id: Column[int] = Column(Integer, primary_key=True)

    # FK
    id_financial_ae: Column[int] = Column(
        Integer,
        ForeignKey("financial_ae.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    montant: Column[float] = Column(Float)
    annee: Column[int] = Column(Integer, nullable=False)

    def __init__(self, montant: float, annee: int):
        self.montant = montant
        self.annee = annee
