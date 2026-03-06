from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from sqlalchemy import Column, Integer, String, Text


class CentreCouts(_Audit, _SyncedWithGrist, _PersistenceBaseModelInstance()):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "ref_centre_couts"
    id: Column[int] = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)
    code_postal: Column[str] = Column(String)
    code_departement: Column[str] = Column(String(5), nullable=True)
    ville: Column[str] = Column(String)

    def __setattr__(self, key, value):
        if key == "code" and isinstance(value, str) and value.startswith("BG00/"):
            value = value[5:]
        super().__setattr__(key, value)
