from app import db, ma
from marshmallow import fields
from sqlalchemy import Column, String


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

    name = fields.String(required=True)
