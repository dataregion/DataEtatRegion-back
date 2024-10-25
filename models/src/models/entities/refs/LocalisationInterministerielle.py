from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.refs.Commune import Commune
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped


class LocalisationInterministerielle(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_localisation_interministerielle"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    site: Column[str] = Column(String)
    description: Column[str] = Column(Text)
    niveau: Column[str] = Column(String)
    code_parent = Column(String)

    # FK
    commune_id = Column(Integer, ForeignKey("ref_commune.id"), nullable=True)
    commune: Mapped[Commune] = relationship("Commune", lazy="select")
