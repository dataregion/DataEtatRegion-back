from datetime import datetime

from sqlalchemy import Column, Integer, String
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from app.models.demarches.demarche import Demarche


class Dossier(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "dossiers"
    __bind_key__ = "demarches_simplifiees"

    number: Column[int] = Column(Integer, primary_key=True, nullable=False)
    state: Column[str] = Column(String, nullable=False)
    date_derniere_modification: Column[datetime] = Column(DateTime, nullable=False)
    n_ej: Column[str] = Column(String, nullable=False)
    siret: Column[str] = Column(String, nullable=False)

    demarche_id: Column[int] = Column(Integer, ForeignKey("demarche.id"), nullable=False)
    demarche: Mapped[Demarche] = relationship("Demarche", lazy="select")


class DossierSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Dossier
