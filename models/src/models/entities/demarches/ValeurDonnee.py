from models import _PersistenceBaseModelInstance
from models.entities.demarches.Donnee import Donnee
from models.entities.demarches.Dossier import Dossier
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship


from dataclasses import dataclass


@dataclass
class ValeurDonnee(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "valeurs_donnees"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)

    dossier_number: Column[int] = Column(
        Integer, ForeignKey("dossiers.number", ondelete="CASCADE"), nullable=False
    )
    dossier: Mapped[Dossier] = relationship("Dossier", lazy="select")
    donnee_id: Column[int] = Column(
        Integer, ForeignKey("donnees.id", ondelete="CASCADE"), nullable=False
    )
    donnee: Mapped[Donnee] = relationship("Donnee", lazy="select")

    valeur: Column[str] = Column(String, nullable=True)
    additional_data: Column[str] = Column(JSON, nullable=True)
