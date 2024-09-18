from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey

from app import db, ma


@dataclass
class Reconciliation(db.Model):
    """
    Modèle pour stocker les réconciliations entre les dossiers DS et les lignes financial AE
    """

    __tablename__ = "reconciliations"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    dossier_number: Column[int] = Column(Integer, ForeignKey("dossiers.number", ondelete="CASCADE"), nullable=False)
    financial_ae_id: Column[int] = Column(Integer, nullable=False, index=True, unique=True)
    date_reconciliation: Column[datetime] = Column(DateTime, nullable=False)


class ReconciliationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Reconciliation
