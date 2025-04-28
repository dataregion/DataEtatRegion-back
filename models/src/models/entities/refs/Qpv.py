from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.refs.QpvCommune import QpvCommune
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped, relationship
from shapely.wkt import loads as wkt_loads
from geoalchemy2 import Geometry


class Qpv(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_qpv"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)

    label_commune: Column[str] = Column(String)

    annee_decoupage = Column(Integer, nullable=True, autoincrement=False)

    geom = Column(Geometry("GEOMETRY"), nullable=True)
    centroid = Column(Geometry("POINT"), nullable=True)
    
    communes = relationship("Commune", secondary=QpvCommune.__table__, backref="commune_qpvs", viewonly=True)


# Event listener to automatically calculate the centroid
@listens_for(Qpv, "before_insert")
@listens_for(Qpv, "before_update")
def calculate_centroid(mapper, connection, target):
    """Automatically calculate the centroid of the geom column."""
    if target.geom is not None:
        # Load the geometry as a Shapely object
        geom_shape = wkt_loads(target.geom)
        # Calculate the centroid
        centroid = geom_shape.centroid
        # Store the centroid back as WKT
        target.centroid = f"SRID=4326;{centroid.wkt}"