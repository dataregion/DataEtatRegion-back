from app import db
from models.entities.demarches.Type import Type


class TypeService:
    @staticmethod
    def get_or_create(type_name: str) -> Type:
        """
        Retourne un type de champ (création si non présent en BDD)
        :param type_name: Nom du type de champ
        :return: Type
        """
        stmt = db.select(Type).where(Type.name == type_name)
        type = db.session.execute(stmt).scalar_one_or_none()
        if type is not None:
            return type
        type = Type(**{"name": type_name})
        db.session.add(type)
        db.session.flush()
        return type
