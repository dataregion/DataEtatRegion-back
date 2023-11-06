from sqlalchemy import Column, String, Text, Integer

from app import db
from app.models.common.Audit import Audit


class NomenclatureFrance2030(Audit, db.Model):
    """
    Nomenclature spécifique france 2030
    """

    __tablename__ = "nomenclature_france_2030"
    # code correspond au levier/objectifs
    code: Column[str] = Column(String, primary_key=True)
    numero: int = Column(Integer, nullable=False)
    mot: Column[str] = Column(String(255), nullable=False)
    phrase: str = Column(Text, nullable=False)
