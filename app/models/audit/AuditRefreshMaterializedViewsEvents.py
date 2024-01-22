from datetime import datetime
from app import db
from sqlalchemy import Column, DateTime, Integer, String
from enum import StrEnum, auto


class RefreshMaterializedViewsEvent(StrEnum):
    BEGIN = auto()
    ENDED = auto()


class AuditRefreshMaterializedViewsEvents(db.Model):
    """
    Modèle pour stocker les evenements de rafraichissement des vues materialisées
    """

    __tablename__ = "audit_refresh_materialized_views"
    __bind_key__ = "audit"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    event: Column[str] = Column(String, nullable=False)
    date: Column[datetime] = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    @staticmethod
    def create(event: RefreshMaterializedViewsEvent) -> "AuditRefreshMaterializedViewsEvents":
        """Crée un row qui représente un evenement de rafraichissement de vue materialisées"""
        _evt = str(event)

        model = AuditRefreshMaterializedViewsEvents()
        model.event = _evt  # type: ignore

        return model
