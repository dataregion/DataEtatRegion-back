from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from sqlalchemy import Column, Integer, String


class Arrondissement(_Audit, _SyncedWithGrist, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_arrondissement"
    id: Column[int] = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)

    code_region: Column[str] = Column(String)
    code_departement: Column[str] = Column(String)

    label: Column[str] = Column(String)

    @staticmethod
    def exclude_schema():
        """Combine les exclusions de _Audit et _SyncedWithGrist."""
        return _Audit.exclude_schema() + _SyncedWithGrist.exclude_schema()
