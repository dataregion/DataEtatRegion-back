import logging

from app import db
from app.models.demarches.donnee import Donnee
from app.services.demarches.sections import SectionService
from app.services.demarches.types import TypeService

logger = logging.getLogger(__name__)


class DonneeService:
    @staticmethod
    def find_by_demarche(demarche_number: int) -> list[Donnee]:
        stmt = db.select(Donnee).where(Donnee.demarche_number == demarche_number)
        return db.session.execute(stmt).scalars()

    @staticmethod
    def get_or_create(champ: dict, section_name: str, demarche_number: int) -> Donnee:
        """
        Retourne un champ par section et démarche (création si non présent en BDD)
        :param champ: Caractéristiques du champ
        :param section_name: Section (champ ou annotation ...)
        :param demarche_number: Numéro de la démarche associée au champ
        :return: Donnee
        """
        stmt = db.select(Donnee).where(Donnee.id_ds == champ["id"])
        donnee = db.session.execute(stmt).scalar_one_or_none()
        if donnee is not None:
            return donnee
        section = SectionService.get_or_create(section_name)
        type = TypeService.get_or_create(champ["__typename"])
        donnee = Donnee(
            **{
                "id_ds": champ["id"],
                "demarche_number": demarche_number,
                "section_name": section.name,
                "type_name": type.name,
                "label": champ["label"],
            }
        )
        db.session.add(donnee)
        db.session.flush()
        return donnee
