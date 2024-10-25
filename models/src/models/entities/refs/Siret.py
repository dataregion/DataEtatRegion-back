from models import _PersistenceBaseModelInstance
from models.entities.refs.CategorieJuridique import CategorieJuridique
from models.entities.refs.Commune import Commune
from models.entities.common.Audit import _Audit
from models.entities.refs.Qpv import Qpv
from sqlalchemy import JSON, Column, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, relationship

JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Siret(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_siret"
    id = Column(Integer, primary_key=True)
    # code siret
    code: Column[str] = Column(String, unique=True, nullable=False)

    # FK
    code_commune = Column(String, ForeignKey("ref_commune.code"), nullable=True)
    categorie_juridique = Column(
        String, ForeignKey("ref_categorie_juridique.code"), nullable=True
    )
    code_qpv = Column(String, ForeignKey("ref_qpv.code"), nullable=True)

    denomination = Column(String)
    adresse = Column(String)
    # Ajout de la partie Naf
    naf = Column(JSONVariant, nullable=True)

    ref_commune: Mapped[Commune] = relationship("Commune", lazy="select")
    ref_qpv: Mapped[Qpv] = relationship("Qpv", lazy="joined")
    ref_categorie_juridique: Mapped[CategorieJuridique] = relationship(
        "CategorieJuridique", lazy="select", uselist=False
    )
    type_categorie_juridique = association_proxy("ref_categorie_juridique", "type")
