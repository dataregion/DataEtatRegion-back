from app import db
from sqlalchemy import Column, Integer, String


class AuditInsertFinancialTasks(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "audit_insert_financial_tasks"
    __bind_key__ = "audit"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    fichier_ae: Column[str] = Column(String, nullable=False)
    fichier_cp: Column[str] = Column(String, nullable=False)
    source_region: Column[str] = Column(String, nullable=False)
    annee: Column[int] = Column(Integer, nullable=False)
    username: Column[str] = Column(String, nullable=False)
