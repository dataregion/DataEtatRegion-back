from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from app.models.demarches.donnee import Donnee
from app.models.demarches.dossier import Dossier


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

    valeur: Column[str] = Column(String, nullable=False)


class DonneeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ValeurDonnee
