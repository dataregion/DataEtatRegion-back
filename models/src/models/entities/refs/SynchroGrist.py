from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Boolean, Column, Integer, String, Text


class SynchroGrist(_PersistenceBaseModelInstance()):
    __tablename__ = "synchro_grist"

    id = Column(Integer, primary_key=True)

    grist_doc_id: Column[str] = Column(String)
    grist_table_id: Column[str] = Column(String)
    grist_table_name: Column[str] = Column(String, unique=True)
