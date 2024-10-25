from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.hybrid import hybrid_property


import dataclasses
import re


@dataclasses.dataclass
class DomaineFonctionnel(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_domaine_fonctionnel"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    @hybrid_property
    def code_programme(self) -> str | None:
        """
        Retourne le code programme associé
        :return:
        """
        if bool(self.code) and isinstance(self.code, str):
            matches = re.search(r"^(\d{4})(-)?", self.code)
            if matches is not None:
                return matches.group(1)[1:]
        return None
