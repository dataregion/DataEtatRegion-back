from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, String, Text


class Ministere(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_ministere"
    code: Column[str] = Column(String, primary_key=True)
    sigle_ministere: Column[str] = Column(String, nullable=True)
    label: Column[str] = Column(String, nullable=False)
    description: Column[str] = Column(Text)
