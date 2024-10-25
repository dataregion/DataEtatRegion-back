from models import _PersistenceBaseModelInstance
from sqlalchemy import JSON, Column, DateTime, Integer, String


from dataclasses import dataclass
from datetime import datetime


@dataclass
class Demarche(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les démarches DS
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
    date_import: Column[datetime] = Column(DateTime, nullable=True)
    reconciliation: Column[str] = Column(JSON, nullable=True)
    affichage: Column[str] = Column(JSON, nullable=True)
