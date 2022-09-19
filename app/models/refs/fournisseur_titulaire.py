from sqlalchemy import Column, String, Text

from app import db

class FournisseurTitulaire(db.Model):
    __tablename__ = 'ref_fournisseur_titulaire'
    id = db.Column(db.Integer, primary_key=True)
    code: str = Column(String, unique=True, nullable=False)
    label: str = Column(String)
    description: str = Column(Text)