from sqlalchemy import Column, String

from app import db, ma
from app.models.common.Audit import Audit


class Arrondissement(Audit, db.Model):
    __tablename__ = "ref_arrondissement"
    id: Column[int] = Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)

    code_region: Column[str] = Column(String)
    code_departement: Column[str] = Column(String)

    label: Column[str] = Column(String)


class ArrondissementSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Arrondissement
        exclude = Arrondissement.exclude_schema()
