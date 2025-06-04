from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text


class Theme(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_theme"

    id = Column(Integer, primary_key=True)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    synchro_grist_id = Column(Integer, ForeignKey("synchro_grist.id"), nullable=True)

    grist_row_id: Column[int] = Column(Integer, unique=True)
    is_deleted: Column[bool] = Column(Boolean, default=False, server_default="FALSE")