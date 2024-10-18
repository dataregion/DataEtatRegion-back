from datetime import date
from marshmallow import fields
from sqlalchemy import Column, String, Boolean, Date
from sqlalchemy.orm import relationship, Mapped

from app.models.refs.arrondissement import Arrondissement  # noqa: F401

from app import db, ma
from app.models.common.Audit import Audit


class Commune(Audit, db.Model):
    __tablename__ = "ref_commune"
    id = db.Column(db.Integer, primary_key=True)

    code: Column[str] = Column(String, unique=True, nullable=False)
    label_commune: Column[str] = Column(String)

    code_crte: Column[str] = Column(String, nullable=True)
    label_crte: Column[str] = Column(String)

    code_region: Column[str] = Column(String)
    label_region: Column[str] = Column(String)

    code_epci: Column[str] = Column(String)
    label_epci: Column[str] = Column(String)

    code_departement: Column[str] = Column(String)
    label_departement: Column[str] = Column(String)

    is_pvd: Column[bool] = Column(Boolean, nullable=True)
    date_pvd: Column[date] = Column(Date, nullable=True)

    is_acv: Column[bool] = Column(Boolean, nullable=True)
    date_acv: Column[date] = Column(Date, nullable=True)

    # FK
    code_arrondissement: Column[str] = Column(String, db.ForeignKey("ref_arrondissement.code"), nullable=True)
    ref_arrondissement: Mapped[Arrondissement] = relationship("Arrondissement", lazy="joined")


class CommuneSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Commune
        exclude = ("id",)

    code = fields.String()
    label_commune = fields.String()
