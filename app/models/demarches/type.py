from dataclasses import dataclass
from app import db, ma
from sqlalchemy import Column, String


@dataclass
class Type(db.Model):
    """
    Modèle pour stocker les tâches d'insert de données financières à effectuer
    """

    __tablename__ = "types"
    __bind_key__ = "demarches_simplifiees"

    name: Column[str] = Column(String, primary_key=True, nullable=False)
    type: Column[str] = Column(String, nullable=True)


class TypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Type
