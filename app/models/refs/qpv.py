from app import db
from sqlalchemy import Column, String
from app.models.common.Audit import Audit


class Qpv(Audit, db.Model):
    __tablename__ = "ref_qpv"
    id = db.Column(db.Integer, primary_key=True)
    code: str = Column(String, unique=True, nullable=False)
    label: str = Column(String)

    label_commune: str = Column(String)
