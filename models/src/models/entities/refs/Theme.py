from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from sqlalchemy import Column, Integer, String, Text


class Theme(_Audit, _SyncedWithGrist, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_theme"

    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, nullable=True)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)
