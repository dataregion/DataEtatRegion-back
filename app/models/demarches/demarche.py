from app import db, ma

from marshmallow import fields

from sqlalchemy import Column, Integer, String


class Demarche(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "demarches"
    __bind_key__ = "demarches_simplifiees"

    number: Column[int] = Column(Integer, primary_key=True, nullable=False)
    title: Column[str] = Column(String, nullable=False)


class DemarcheSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Demarche
    number = fields.Integer(required=True)
    title = fields.String(required=True)
