import dataclasses
import re

from sqlalchemy import Column, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import fields


from app import db, ma
from app.models.common.Audit import Audit


@dataclasses.dataclass
class DomaineFonctionnel(Audit, db.Model):
    __tablename__ = "ref_domaine_fonctionnel"
    id = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: str = Column(Text)

    @hybrid_property
    def code_programme(self) -> str | None:
        """
        Retourne le code programme associé
        :return:
        """
        if bool(self.code) and isinstance(self.code, str):
            matches = re.search(r"^(\d{4})(-)?", self.code)
            if matches is not None:
                return matches.group(1)[1:]
        return None


class DomaineFonctionnelSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = DomaineFonctionnel
        exclude = ("id",) + DomaineFonctionnel.exclude_schema()

    code_programme = fields.String()
    label = fields.String()
    description = fields.String()
