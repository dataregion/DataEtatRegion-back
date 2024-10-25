from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String, Text


class FournisseurTitulaire(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_fournisseur_titulaire"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)