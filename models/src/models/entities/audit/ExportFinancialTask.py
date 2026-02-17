from datetime import datetime
from typing import Literal

from sqlalchemy import Column, DateTime, Integer, String

from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.value_objects.export_api import ExportTarget

ExportFinancialTaskStatus = Literal["PENDING", "RUNNING", "DONE", "FAILED", "ARCHIVED"]


class ExportFinancialTask(_Audit, _PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les exports financiers asynchrones.
    Une entrée est créée à chaque demande d'export utilisateur.
    """

    __tablename__ = "audit_export_financial"
    __bind_key__ = "audit"
    __table_args__ = {"schema": "audit"}

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    """ID technique"""

    prefect_run_id: Column[str] = Column(String, nullable=True, unique=True)
    """ID du run Prefect associé à cette tâche d'export."""

    file_path: Column[str] = Column(String, nullable=True)
    """Chemin vers lequel aller récupérer le fichier exporté une fois l'import terminé."""

    target_format: Column[ExportTarget] = Column(String, nullable=True, doc="csv | xlsx | ods | to-grist")
    """Le format de l'export"""

    status: Column[ExportFinancialTaskStatus] = Column(
        String,
        nullable=False,
        default="PENDING",
        doc="PENDING | RUNNING | DONE | FAILED | ARCHIVED",
    )
    """Status de l'export"""

    username: Column[str] = Column(String, nullable=False)
    """Email de l'utilisateur ayant lancé l'export."""

    name: Column[str] = Column(String, nullable=True)

    started_at: Column[datetime] = Column(DateTime(timezone=True), nullable=True)
    completed_at: Column[datetime] = Column(DateTime(timezone=True), nullable=True)

    @staticmethod
    def create(username: str, prefect_id: str, name: str):
        """Crée une nouvelle tâche d'export financier."""
        return ExportFinancialTask(username=username, prefect_run_id=prefect_id, name=name, status="PENDING")
