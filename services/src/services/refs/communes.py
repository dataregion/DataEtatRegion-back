from typing import Iterable

from models.entities.refs.Commune import Commune
from sqlalchemy import or_, update
from sqlalchemy.orm import Session


def select_communes_id(session: Session, codes: Iterable[str]):
    stmt = session.query(Commune.id, Commune.code).filter(Commune.code.in_(list(codes)))
    return stmt.all()


def set_communes_non_pvd(session: Session) -> None:
    session.execute(
        update(Commune)
        .where(or_(Commune.is_pvd.is_(True), Commune.date_pvd.is_not(None)))
        .values(is_pvd=False, date_pvd=None)
    )


def set_communes_non_acv(session: Session) -> None:
    session.execute(
        update(Commune)
        .where(or_(Commune.is_acv.is_(True), Commune.date_acv.is_not(None)))
        .values(is_acv=False, date_acv=None)
    )


def set_communes_pvd(session: Session, updates_to_commit: list[dict]) -> None:
    session.execute(update(Commune), updates_to_commit)


def set_communes_acv(session: Session, updates_to_commit: list[dict]) -> None:
    session.execute(update(Commune), updates_to_commit)
