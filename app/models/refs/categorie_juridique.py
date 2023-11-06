from sqlalchemy import Column, String

from app import db
from app.models.common.Audit import Audit


class CategorieJuridique(Audit, db.Model):
    __tablename__ = "ref_categorie_juridique"
    id = db.Column(db.Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    type: Column[str] = Column(String)
    label: Column[str] = Column(String)
