from dataclasses import dataclass
from sqlalchemy import Column, String, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from marshmallow import fields
from app.models.demarches.donnee import Donnee
from app.models.demarches.dossier import Dossier

@dataclass
class ValeurDonnee(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "valeurs_donnees"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)

    dossier_number: Column[int] = Column(Integer, ForeignKey("dossiers.number", ondelete="CASCADE"), nullable=False)
    dossier: Mapped[Dossier] = relationship("Dossier", lazy="select")
    donnee_id: Column[int] = Column(Integer, ForeignKey("donnees.id", ondelete="CASCADE"), nullable=False)
    donnee: Mapped[Donnee] = relationship("Donnee", lazy="select")

    valeur: Column[str] = Column(String, nullable=True)
    additional_data: Column[str] = Column(JSON, nullable=True)


class ValeurDonneeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ValeurDonnee
        exclude = ("additional_data",)

    dossier_number = fields.Integer()
    donnee_id = fields.Integer()
    valeur = fields.String()
    
