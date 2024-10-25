from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String, Text


class GroupeMarchandise(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_groupe_marchandise"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    domaine: Column[str] = Column(String)
    segment: Column[str] = Column(String)

    # mutualisation avec compte_general
    code_pce: Column[str] = Column(String)
    label_pce: Column[str] = Column(String)
