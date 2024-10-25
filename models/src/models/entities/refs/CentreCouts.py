from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String, Text


class CentreCouts(_Audit, _PersistenceBaseModelInstance()):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "ref_centre_couts"
    id: Column[int] = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)
    code_postal: Column[str] = Column(String)
    ville: Column[str] = Column(String)

    def __setattr__(self, key, value):
        if key == "code" and isinstance(value, str) and value.startswith("BG00/"):
            value = value[5:]
        super().__setattr__(key, value)
