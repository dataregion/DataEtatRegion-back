from app import db, ma
from sqlalchemy import Column, String
from sqlalchemy.event import listens_for
from marshmallow import fields
from app.models.common.Audit import Audit
from geoalchemy2 import Geometry
from shapely.wkt import loads as wkt_loads
from app.models.utils import GeometryField


class Qpv(Audit, db.Model):
    __tablename__ = "ref_qpv"
    id = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    label_commune: Column[str] = Column(String)

    annee_decoupage = db.Column(db.Integer, nullable=True, autoincrement=False)

    geom = Column(Geometry("GEOMETRY"), nullable=True)
    centroid = Column(Geometry("POINT"), nullable=True)


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


class QpvSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Qpv
        exclude = ("id",) + Qpv.exclude_schema()

    code = fields.String()
    label = fields.String()
    label_commune = fields.String()
    annee_decoupage = fields.Integer()
    geom = GeometryField(dump_only=True)
    centroid = GeometryField(dump_only=True)
