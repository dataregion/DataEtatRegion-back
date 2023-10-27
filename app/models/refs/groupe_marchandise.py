from marshmallow import fields
from sqlalchemy import Column, String, Text

from app import db, ma
from app.models.common.Audit import Audit


class GroupeMarchandise(Audit, db.Model):
    __tablename__ = "ref_groupe_marchandise"
    id = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: str = Column(Text)

    domaine: Column[str] = Column(String)
    segment: Column[str] = Column(String)

    # mutualisation avec compte_general
    code_pce: Column[str] = Column(String)
    label_pce: Column[str] = Column(String)


class GroupeMarchandiseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = GroupeMarchandise
        exclude = ("id",) + GroupeMarchandise.exclude_schema()

    label = fields.String()
    code = fields.String()
    description = fields.String()
    domaine = fields.String()
    segment = fields.String()
    code_pce = fields.String()
    label_pce = fields.String()
