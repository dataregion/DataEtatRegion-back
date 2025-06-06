from models import _PersistenceBaseModelInstance
from sqlalchemy import Column, String


from dataclasses import dataclass


@dataclass
class Section(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "sections"
    __bind_key__ = "demarches_simplifiees"

    name: Column[str] = Column(String, primary_key=True, nullable=False)
