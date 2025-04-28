from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped, relationship
from shapely.wkt import loads as wkt_loads
from geoalchemy2 import Geometry


class QpvCommune(_PersistenceBaseModelInstance()):
    __tablename__ = "ref_join_qpv_commune"
    id = Column(Integer, primary_key=True)

    qpv_id: Column[int] = Column(Integer, ForeignKey("ref_qpv.id"), nullable=False)
    commune_id: Column[int] = Column(Integer, ForeignKey("ref_commune.id"), nullable=False)
