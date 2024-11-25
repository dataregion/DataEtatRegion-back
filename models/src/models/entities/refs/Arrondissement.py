from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String


class Arrondissement(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_arrondissement"
    id: Column[int] = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)

    code_region: Column[str] = Column(String)
    code_departement: Column[str] = Column(String)

    label: Column[str] = Column(String)
