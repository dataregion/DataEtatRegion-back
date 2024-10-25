from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String, Text, func
from sqlalchemy.ext.hybrid import hybrid_property


import re


class ReferentielProgrammation(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_programmation"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    @hybrid_property
    def code_programme(self) -> str | None:  # type: ignore
        """
        Retourne le code programme associé
        :return:
        """
        if bool(self.code) and isinstance(self.code, str):
            matches = re.search(r"^(\d{4})(.*)", self.code)
            if matches is not None:
                return matches.group(1)[1:]
        return None

    @code_programme.expression
    def code_programme(cls):
        """
        Expression pour utiliser le code_programme dans une requête SQLAlchemy
        :return:
        """
        return func.substring(func.substring(cls.code, 1, 4), 2).label("code_programme")
