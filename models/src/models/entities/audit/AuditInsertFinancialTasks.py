from models import _PersistenceBaseModelInstance
from sqlalchemy import Column, Integer, String


class AuditInsertFinancialTasks(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "audit_insert_financial_tasks"
    __bind_key__ = "audit"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    session_token: Column[str] = Column(String, nullable=True, unique=True)
    """ session token de l'import provenant de l'outil d'upload. Permet de regrouper
      le fichier AE et CP téléverser via TUS unitairement"""

    fichier_ae: Column[str] = Column(String, nullable=True)
    fichier_cp: Column[str] = Column(String, nullable=True)
    source_region: Column[str] = Column(String, nullable=False)
    annee: Column[int] = Column(Integer, nullable=False)
    username: Column[str] = Column(String, nullable=False)

    application_clientid: Column[str] = Column(String, nullable=True)
    """clientid associé à l'outil qui a lancé l'évenement d'import si import manuel"""
