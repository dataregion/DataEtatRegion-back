from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String


class Qpv(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_qpv"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)

    label_commune: Column[str] = Column(String)