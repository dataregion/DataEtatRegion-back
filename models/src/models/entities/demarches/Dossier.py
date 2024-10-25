from models import _PersistenceBaseModelInstance
from models.entities.demarches.Demarche import Demarche
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship


from dataclasses import dataclass
from datetime import datetime


@dataclass
class Dossier(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "dossiers"
    __bind_key__ = "demarches_simplifiees"

    number: Column[int] = Column(Integer, primary_key=True, nullable=False)
    demarche_number: Column[int] = Column(
        Integer, ForeignKey("demarches.number", ondelete="CASCADE"), nullable=False
    )
    revision_id: Column[str] = Column(String, nullable=False)
    state: Column[str] = Column(String, nullable=False)
    siret: Column[str] = Column(String, nullable=True)
    date_depot: Column[datetime] = Column(DateTime, nullable=False)
    date_derniere_modification: Column[datetime] = Column(DateTime, nullable=False)

    demarche: Mapped[Demarche] = relationship("Demarche", lazy="select")
