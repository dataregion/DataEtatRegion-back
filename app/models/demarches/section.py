from app import db, ma
from sqlalchemy import Column, Integer, String


class Section(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "sections"
    __bind_key__ = "demarches_simplifiees"

    name: Column[str] = Column(String, primary_key=True, nullable=False)


class SectionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Section
