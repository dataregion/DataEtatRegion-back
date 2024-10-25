from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String


class CategorieJuridique(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_categorie_juridique"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    type: Column[str] = Column(String)
    label: Column[str] = Column(String)