from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from app.models.demarches.demarche import Demarche


class Donnee(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "donnees"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)

    demarche_number: Column[int] = Column(Integer, ForeignKey("demarches.number", ondelete="CASCADE"), nullable=False)
    demarche: Mapped[Demarche] = relationship("Demarche", lazy="select")
    section_name: Column[str] = Column(String, ForeignKey("sections.name", ondelete="CASCADE"), nullable=False)
    type_name: Column[str] = Column(String, ForeignKey("types.name", ondelete="CASCADE"), nullable=False)

    label: Column[str] = Column(String, nullable=False)


class DonneeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Donnee
