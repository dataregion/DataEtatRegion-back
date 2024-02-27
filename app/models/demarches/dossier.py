from datetime import datetime

from marshmallow import fields

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

    demarche_number: Column[int] = Column(Integer, ForeignKey("demarches.number"), nullable=False)
    demarche: Mapped[Demarche] = relationship("Demarche", lazy="select")

    state: Column[str] = Column(String, nullable=False)
    date_derniere_modification: Column[datetime] = Column(DateTime, nullable=False)
    siret: Column[str] = Column(String, nullable=False)


class DossierSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Dossier
    number = fields.Integer(required=True)
    demarche_number = fields.Integer(required=True)
    state = fields.Boolean(required=True)
    date_derniere_modification = fields.DateTime(required=True)
    siret = fields.String(required=True)
