import logging
from app import db
from models.entities.refs.Commune import Commune
from sqlalchemy import and_, Date, update

logger = logging.getLogger(__name__)


def select_communes_id(codes: str) -> Commune:
    """
    Retourne l'objet Commune à partir du code et du nom de la commune
    :param code: Code de la commune
    :param label: Nom de la commune
    :return: Commune
    """
    stmt = db.select(Commune.id, Commune.code)
    stmt = stmt.where(Commune.code.in_(codes))
    return db.session.execute(stmt).fetchall()


def select_commune(code: str) -> Commune:
    """
    Retourne l'objet Commune à partir du code et du nom de la commune
    :param code: Code de la commune
    :param label: Nom de la commune
    :return: Commune
    """
    stmt = db.select(Commune)
    stmt = stmt.where(and_(Commune.code == code))
    return db.session.execute(stmt).scalar_one()


def set_pvd(commune: Commune, date_signature: Date = None) -> None:
    """
    Définis une commune comme PVD à partie d'une date spécifiée
    :param commune: Commune à modifier
    :param date_signature_pvd: Date à laquelle la commune a été désignée comme PVD
    :return: None
    """
    commune.is_pvd = True
    commune.date_pvd = date_signature
    db.session.commit()


def set_communes_non_pvd() -> None:
    """
    Reset toutes les communes comme non PVD
    :return: None
    """
    Commune.query.update({Commune.is_pvd: False, Commune.date_pvd: None})
    db.session.commit()


def set_communes_pvd(updates_to_commit: [dict[str, any]]) -> None:
    """
    Set is_pvd = True et date_pvd = :date_pvd des communes en fonction des id précisés dans updates_to_commit
    :return: None
    """
    db.session.execute(update(Commune), updates_to_commit)
    db.session.commit()


def set_acv(commune: Commune, date_signature: Date = None) -> None:
    """
    Définis une commune comme ACV à partie d'une date spécifiée
    :param commune: Commune à modifier
    :param date_signature_pvd: Date à laquelle la commune a été désignée comme PVD
    :return: None
    """
    commune.is_acv = True
    commune.date_acv = date_signature
    db.session.commit()


def set_communes_non_acv() -> None:
    """
    Reset toutes les communes comme non ACV
    :return: None
    """
    Commune.query.update({Commune.is_acv: False, Commune.date_acv: None})
    db.session.commit()


def set_communes_acv(updates_to_commit: [dict[str, any]]) -> None:
    """
    Set is_acv = True et date_acv = :date_acv des communes en fonction des id précisés dans updates_to_commit
    :return: None
    """
    db.session.execute(update(Commune), updates_to_commit)
    db.session.commit()
