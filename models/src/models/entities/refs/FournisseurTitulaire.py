from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from sqlalchemy import Column, Integer, String, Text


class FournisseurTitulaire(_Audit, _SyncedWithGrist, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_fournisseur_titulaire"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    @staticmethod
    def exclude_schema():
        """Combine les exclusions de _Audit et _SyncedWithGrist."""
        return _Audit.exclude_schema() + _SyncedWithGrist.exclude_schema()
