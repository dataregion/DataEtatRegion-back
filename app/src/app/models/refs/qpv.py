from app import db, ma
from sqlalchemy import Column, String
from marshmallow import fields
from app.models.common.Audit import Audit


class Qpv(Audit, db.Model):
    __tablename__ = "ref_qpv"
    id = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)

    label_commune: Column[str] = Column(String)


class QpvSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Qpv
        exclude = ("id",) + Qpv.exclude_schema()

    code = fields.String()
    label = fields.String()
    label_commune = fields.String()
