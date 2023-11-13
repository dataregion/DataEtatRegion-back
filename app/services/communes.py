import logging
from app import db
from app.models.refs.commune import Commune
from sqlalchemy import and_

logger = logging.getLogger(__name__)


def select_commune(code: str, label: str) -> Commune:
  """
  Retourne l'objet Commune à partir du code et du nom de la commune
  :param code: Code de la commune
  :param label: Nom de la commune
  :return: Commune
  """
  stmt = db.select(Commune)
  stmt = stmt.where(and_(Commune.code == code, Commune.label_commune == label))
  return db.session.execute(stmt).scalar_one()


def set_pvd(self, commune: Commune) -> None:
  """
  Définis une commune comme PVD à partie d'une date spécifiée
  :param commune: Commune à modifier
  :param date_signature_pvd: Date à laquelle la commune a été désignée comme PVD
  :return: None
  """
  commune.is_pvd = True
  print(f"PVD : {commune.code} {commune.label_commune}")
  db.session.commit()


def set_communes_non_pvd() -> None:
    """
    Reset toutes les communes comme non PVD
    :return: None
    """
    Commune.query.update({Commune.is_pvd: None}) 
    db.session.commit()
