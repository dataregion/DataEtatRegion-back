import logging

from app import db, cache
from app.services.demarches.sections import SectionService
from app.services.demarches.types import TypeService
from models.entities.demarches.Donnee import Donnee

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
        donnee = DonneeService.get_donnee(champ["id"], demarche_number)
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

    @staticmethod
    @cache.memoize(timeout=60)
    def get_donnee(id_ds_donnee: int, demarche_number: int) -> Donnee:
        stmt = db.select(Donnee).where(Donnee.id_ds == id_ds_donnee).where(Donnee.demarche_number == demarche_number)
        return db.session.execute(stmt).scalar_one_or_none()
