from contextlib import contextmanager
import logging

from functools import lru_cache
from typing import Literal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apis.config.current import get_config
from services.utilities import sqlalchemy_pretty_printer
from services.utilities.observability import cache_stats


def make_main_engine():
    db_url = get_config().sqlalchemy_database_uri
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql)
    return engine


def make_audit_engine():
    db_url = get_config().sqlalchemy_database_uri_audit
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql)
    return engine


EngineName = Literal["audit", "main"]


@cache_stats()
@lru_cache
def get_sesion_maker(engine_name: EngineName):
    main_engine = make_main_engine()
    audit_engine = make_audit_engine()

    engines = {
        "main": main_engine,
        "audit": audit_engine,
    }

    if get_config().print_sql:
        _format = "%(asctime)s.%(msecs)03d : %(levelname)s : %(message)s"
        logging.basicConfig(format=_format, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO, force=True)
        sqlalchemy_pretty_printer.setup(format=_format)
    selected_engine = engines[engine_name]
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=selected_engine)
    return SessionLocal


def get_session_main():
    session_maker = get_sesion_maker("main")
    session = session_maker()
    try:
        yield session
    finally:
        session.close()


def get_session_audit():
    session_maker = get_sesion_maker("audit")
    session = session_maker()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_audit_scope():
    session_maker = get_sesion_maker("audit")
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
