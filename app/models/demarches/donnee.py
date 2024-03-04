from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from app.models.demarches.demarche import Demarche
from app.models.demarches.section import Section
from app.models.demarches.type import Type


class Donnee(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "donnees"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)

    demarche_number: Column[int] = Column(Integer, ForeignKey("demarches.number"), nullable=False)
    demarche: Mapped[Demarche] = relationship("Demarche", lazy="select")
    section_name: Column[str] = Column(String, ForeignKey("sections.name"), nullable=False)
    section: Mapped[Section] = relationship("Section", lazy="select")
    type_name: Column[str] = Column(String, ForeignKey("types.name"), nullable=False)
    type: Mapped[Type] = relationship("Type", lazy="select")

    label: Column[str] = Column(String, nullable=False)


class DonneeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Donnee
