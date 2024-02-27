import logging

from app import db
from app.models.demarches.demarche import Demarche
from app.models.demarches.dossier import Dossier
from app.models.demarches.donnee import Donnee
from app.models.demarches.section import Section
from app.models.demarches.type import Type
from app.models.demarches.valeur_donnee import ValeurDonnee

logger = logging.getLogger(__name__)



def demarche_exists(number: int) -> bool:
    stmt = db.select(Demarche).where(Demarche.number == number)
    return db.session.execute(stmt).one_or_none() is not None


def save_demarche(demarche: Demarche) -> Demarche:
    """
    Retourne l'objet Commune à partir du code et du nom de la commune
    :param code: Code de la commune
    :param label: Nom de la commune
    :return: Commune
    """
    db.session.add(demarche)
    db.session.commit()
    return demarche


def save_dossier(dossier: Dossier) -> Dossier:
    """
    Retourne l'objet Commune à partir du code et du nom de la commune
    :param code: Code de la commune
    :param label: Nom de la commune
    :return: Commune
    """
    db.session.add(dossier)
    db.session.commit()
    return dossier


def get_or_create_section(section_name: str) -> Section:
    stmt = db.select(Section).where(Section.name == section_name)
    section = db.session.execute(stmt).scalar_one_or_none()
    if section is not None:
        return section
    section = Section(**{
        "name": section_name
    })
    db.session.add(section)
    db.session.commit()
    return section


def get_or_create_type(type_name: str) -> Type:
    stmt = db.select(Type).where(Type.name == type_name)
    type = db.session.execute(stmt).scalar_one_or_none()
    if type is not None:
        return type
    type = Type(**{
        "name": type_name
    })
    db.session.add(type)
    db.session.commit()
    return type


def get_or_create_donnee(champ: dict, section_name: str, demarche_number: int) -> Donnee:
    stmt = db.select(Donnee).where(Donnee.label == champ["label"], Donnee.section_name == section_name, Donnee.type_name == champ["__typename"])
    donnee = db.session.execute(stmt).scalar_one_or_none()
    if donnee is not None:
        return donnee
    section = get_or_create_section(section_name)
    type = get_or_create_type(champ["__typename"])
    donnee = Donnee(**{
        "demarche_number": demarche_number,
        "section_name": section.name,
        "type_name": type.name,
        "label": champ["label"]
    })
    db.session.add(donnee)
    db.session.commit()
    return donnee


def save_valeur_donnee(dossier_number: int, donnee_id: int, value: str) -> ValeurDonnee:
    valeur = ValeurDonnee(**{
        "dossier_number": dossier_number,
        "donnee_id": donnee_id,
        "valeur": value
    })
    db.session.add(valeur)
    db.session.commit()
    return valeur