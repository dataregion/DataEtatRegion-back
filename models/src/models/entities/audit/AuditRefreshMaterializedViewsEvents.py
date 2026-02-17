from datetime import datetime, timezone
from models import _PersistenceBaseModelInstance
from models.value_objects.audit import RefreshMaterializedViewsEvent
from sqlalchemy import Column, DateTime, Integer, String


class AuditRefreshMaterializedViewsEvents(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les evenements de rafraichissement des vues materialisées
    """

    __tablename__ = "audit_refresh_materialized_views"
    __bind_key__ = "audit"
    __table_args__ = {"schema": "audit"}

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    event: Column[str] = Column(String, nullable=False)
    date: Column[datetime] = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    table = Column(String, nullable=True)

    @staticmethod
    def create(event: RefreshMaterializedViewsEvent, table: str) -> "AuditRefreshMaterializedViewsEvents":
        """Crée un row qui représente un evenement de rafraichissement de vue materialisées"""
        _evt = str(event)

        model = AuditRefreshMaterializedViewsEvents()
        model.event = _evt  # type: ignore
        model.table = table  # type: ignore

        return model
