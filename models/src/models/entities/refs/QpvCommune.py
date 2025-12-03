from models import _PersistenceBaseModelInstance
from sqlalchemy import Column, ForeignKey, Integer


class QpvCommune(_PersistenceBaseModelInstance()):
    __tablename__ = "ref_join_qpv_commune"
    id = Column(Integer, primary_key=True)

    qpv_id: Column[int] = Column(Integer, ForeignKey("ref_qpv.id"), nullable=False)
    commune_id: Column[int] = Column(Integer, ForeignKey("ref_commune.id"), nullable=False)
