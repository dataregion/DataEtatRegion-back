from sqlalchemy import String, Text

from app import db, ma
from sqlalchemy import Column

from app.models.common.Audit import Audit


class CentreCouts(Audit, db.Model):
    __table_args__ = {"extend_existing": True}
    __tablename__ = "ref_centre_couts"
    id: int = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: str = Column(Text)
    code_postal: Column[str] = Column(String)
    ville: Column[str] = Column(String)

    def __setattr__(self, key, value):
        if key == "code" and isinstance(value, str) and value.startswith("BG00/"):
            value = value[5:]
        super().__setattr__(key, value)


class CentreCoutsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CentreCouts
        exclude = ("id",) + CentreCouts.exclude_schema()
