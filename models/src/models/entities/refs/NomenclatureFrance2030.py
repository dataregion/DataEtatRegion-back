from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from sqlalchemy import Column, Integer, String, Text


class NomenclatureFrance2030(_Audit, _SyncedWithGrist, _PersistenceBaseModelInstance()):
    """
    Nomenclature spécifique france 2030
    """

    __tablename__ = "nomenclature_france_2030"
    # code correspond au levier/objectifs
    code: Column[str] = Column(String, primary_key=True)
    numero: Column[int] = Column(Integer, nullable=False)
    mot: Column[str] = Column(String(255), nullable=False)
    phrase: Column[str] = Column(Text, nullable=False)

    @staticmethod
    def exclude_schema():
        """Combine les exclusions de _Audit et _SyncedWithGrist."""
        return _Audit.exclude_schema() + _SyncedWithGrist.exclude_schema()
