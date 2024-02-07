from marshmallow import fields
from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, Mapped

from app import db, ma
from app.models.common.Audit import Audit
from app.models.refs.commune import Commune

JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Siret(Audit, db.Model):
    __tablename__ = "ref_siret"
    id = db.Column(db.Integer, primary_key=True)
    # code siret
    code: Column[str] = Column(String, unique=True, nullable=False)

    # FK
    code_commune = Column(String, db.ForeignKey("ref_commune.code"), nullable=True)
    categorie_juridique = Column(String, db.ForeignKey("ref_categorie_juridique.code"), nullable=True)
    code_qpv = Column(String, db.ForeignKey("ref_qpv.code"), nullable=True)

    denomination = Column(String)
    adresse = Column(String)
    # Ajout de la partie Naf
    naf = Column(JSONVariant, nullable=True)

    ref_commune: Mapped[Commune] = relationship("Commune", lazy="select")
    ref_qpv = relationship("Qpv", lazy="joined")
    ref_categorie_juridique = relationship("CategorieJuridique", lazy="select", uselist=False)
    type_categorie_juridique = association_proxy("ref_categorie_juridique", "type")


class SiretSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Siret
        exclude = (
            "id",
            "naf",
            "code",
        ) + Siret.exclude_schema()

    siret = fields.String(attribute="code")
    categorie_juridique = fields.String(attribute="type_categorie_juridique")
    denomination = fields.String()
    adresse = fields.String()
