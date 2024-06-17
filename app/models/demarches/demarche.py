from app import db, ma

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime


class Demarche(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "demarches"
    __bind_key__ = "demarches_simplifiees"

    number: Column[int] = Column(Integer, primary_key=True, nullable=False)
    title: Column[str] = Column(String, nullable=False)
    state: Column[str] = Column(String, nullable=False)
    centre_couts: Column[str] = Column(String, nullable=False)
    domaine_fonctionnel: Column[str] = Column(String, nullable=False)
    referentiel_programmation: Column[str] = Column(String, nullable=False)
    date_creation: Column[datetime] = Column(DateTime, nullable=False)
    date_fermeture: Column[datetime] = Column(DateTime, nullable=True)


class DemarcheSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Demarche
