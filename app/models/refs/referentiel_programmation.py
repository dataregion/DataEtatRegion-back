import re

from sqlalchemy import Column, String, Text
from marshmallow import fields
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func

from app import db, ma
from app.models.common.Audit import Audit


class ReferentielProgrammation(Audit, db.Model):
    __tablename__ = "ref_programmation"
    id = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    @hybrid_property
    def code_programme(self) -> str | None:
        """
        Retourne le code programme associé
        :return:
        """
        if bool(self.code) and isinstance(self.code, str):
            matches = re.search(r"^(\d{4})(.*)", self.code)
            if matches is not None:
                return matches.group(1)[1:]
        return None

    @code_programme.expression
    def code_programme(cls):
        """
        Expression pour utiliser le code_programme dans une requête SQLAlchemy
        :return:
        """
        return func.substring(func.substring(cls.code, 1, 4), 2).label("code_programme")


class ReferentielProgrammationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ReferentielProgrammation
        exclude = ("id",) + ReferentielProgrammation.exclude_schema()

    label = fields.String()
    description = fields.String()
    code_programme = fields.String()
