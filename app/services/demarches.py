import logging

from app import db
from app.models.demarches.demarche import Demarche
from app.models.demarches.dossier import Dossier
from app.models.demarches.donnee import Donnee
from app.models.demarches.section import Section
from app.models.demarches.type import Type
from app.models.demarches.valeur_donnee import ValeurDonnee

logger = logging.getLogger(__name__)


def find_demarche(number: int) -> Demarche:
    """
    Vérifie si une Demarche est présente en BDD
    :param number: Numéro de la démarche à rechercher
    :return: bool
    """
    stmt = db.select(Demarche).where(Demarche.number == number)
    return db.session.execute(stmt).scalar_one_or_none()


def save_demarche(demarche: Demarche) -> Demarche:
    """
    Sauvegarde un objet Demarche
    :param demarche: Objet à sauvegarder
    :return: Demarche
    """
    db.session.add(demarche)
    db.session.flush()
    return demarche


def delete_demarche(demarche: Demarche) -> None:
    """
    Supprime un objet Demarche
    :param Demarche: Démarche à supprimer
    :return: None
    """
    db.session.delete(demarche)
    db.session.flush()
    db.session.commit()


def save_dossier(dossier: Dossier) -> Dossier:
    """
    Sauvegarde un objet Dossier
    :param dossier: Objet à sauvegarder
    :return: Dossier
    """
    db.session.add(dossier)
    db.session.flush()
    return dossier


def get_or_create_section(section_name: str) -> Section:
    """
    Retourne une section (création si non présent en BDD)
    :param section_name: Nom de la section
    :return: Section
    """
    stmt = db.select(Section).where(Section.name == section_name)
    section = db.session.execute(stmt).scalar_one_or_none()
    if section is not None:
        return section
    section = Section(**{"name": section_name})
    db.session.add(section)
    db.session.flush()
    return section


def get_or_create_type(type_name: str) -> Type:
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


def get_or_create_donnee(champ: dict, section_name: str, demarche_number: int) -> Donnee:
    """
    Retourne un champ par section et démarche (création si non présent en BDD)
    :param champ: Caractéristiques du champ
    :param section_name: Section (champ ou annotation ...)
    :param demarche_number: Numéro de la démarche associée au champ
    :return: Donnee
    """
    stmt = db.select(Donnee).where(
        Donnee.label == champ["label"], Donnee.section_name == section_name, Donnee.type_name == champ["__typename"]
    )
    donnee = db.session.execute(stmt).scalar_one_or_none()
    if donnee is not None:
        return donnee
    section = get_or_create_section(section_name)
    type = get_or_create_type(champ["__typename"])
    donnee = Donnee(
        **{
            "demarche_number": demarche_number,
            "section_name": section.name,
            "type_name": type.name,
            "label": champ["label"],
        }
    )
    db.session.add(donnee)
    db.session.flush()
    return donnee


# Nom des champs additionnels à récupérer en fonction du type du champ
_mappingTypes = [
    {"types": ["DateChamp"], "fields": ["date"]},
    {"types": ["DatetimeChamp"], "fields": ["datetime"]},
    {"types": ["CheckboxChamp"], "fields": ["checked"]},
    {"types": ["DecimalNumberChamp"], "fields": ["decimalNumber"]},
    {"types": ["IntegerNumberChamp", "NumberChamp"], "fields": ["integerNumber"]},
    {"types": ["CiviliteChamp"], "fields": ["civilite"]},
    {"types": ["LinkedDropDownListChamp"], "fields": ["primaryValue", "secondaryValue"]},
    {"types": ["MultipleDropDownListChamp"], "fields": ["values"]},
    {"types": ["PieceJustificativeChamp"], "fields": ["files"]},
    {"types": ["AddressChamp"], "fields": ["address"]},
    {"types": ["CommuneChamp"], "fields": ["commune", "departement"]},
    {"types": ["DepartementChamp"], "fields": ["departement"]},
    {"types": ["RegionChamp"], "fields": ["region"]},
    {"types": ["PaysChamp"], "fields": ["pays"]},
    {"types": ["SiretChamp"], "fields": ["etablissement"]},
]


def save_valeur_donnee(dossier_number: int, donnee_id: int, champ: dict) -> ValeurDonnee:
    """
    Créé en BDD une valeur d'un champ pour un dossier
    :param dossier_number: Numéro du dossier associé
    :param donnee_id: ID de la donnée associée
    :param champ: Caractéristique du champ
    :return: Donnee
    """
    # Récupération des données additionnelles en fonction du type du champ
    additional_data = {}
    for mapping in _mappingTypes:
        if champ["__typename"] in mapping["types"]:
            for field in mapping["fields"]:
                additional_data[field] = champ[field]

    # Création de la valeur en BDD
    valeur = ValeurDonnee(
        **{
            "dossier_number": dossier_number,
            "donnee_id": donnee_id,
            "valeur": champ["stringValue"],
            "additional_data": additional_data,
        }
    )
    db.session.add(valeur)
    db.session.flush()
    return valeur


def commit_demarche() -> None:
    """
    Commit tous les changement effectués en BDD
    :return: None
    """
    db.session.commit()
