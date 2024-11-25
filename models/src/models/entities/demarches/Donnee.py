from models import _PersistenceBaseModelInstance
from models.entities.demarches.Demarche import Demarche
from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, relationship


from dataclasses import dataclass


@dataclass
class Donnee(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "donnees"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    id_ds: Column[str] = Column(String, nullable=False)
    label: Column[str] = Column(String, nullable=False)

    demarche_number: Column[int] = Column(
        Integer, ForeignKey("demarches.number", ondelete="CASCADE"), nullable=False
    )
    section_name: Column[str] = Column(
        String, ForeignKey("sections.name", ondelete="CASCADE"), nullable=False
    )
    type_name: Column[str] = Column(
        String, ForeignKey("types.name", ondelete="CASCADE"), nullable=False
    )

    demarche: Mapped[Demarche] = relationship("Demarche", lazy="select")


Index(
    "ix_donnees_id_ds_demarche_number",
    Donnee.id_ds,
    Donnee.demarche_number,
    unique=True,
)
