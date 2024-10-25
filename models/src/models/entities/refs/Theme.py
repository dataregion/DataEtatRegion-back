from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String, Text


class Theme(_Audit, _PersistenceBaseModelInstance()):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "ref_theme"
    id = Column(Integer, primary_key=True)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)