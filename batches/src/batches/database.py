from contextlib import contextmanager
import logging
from typing import Literal

from models import init as init_persistence_module

init_persistence_module()

from functools import lru_cache  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from services.utilities.observability import cache_stats  # noqa: E402
from services.utilities import sqlalchemy_pretty_printer  # noqa: E402

from batches.config.current import get_config  # noqa: E402


def make_main_engine():
    db_url = get_config().sqlalchemy_database_uri
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql)
    return engine


def make_audit_engine():
    db_url = get_config().sqlalchemy_database_uri_audit
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql)
    return engine


def make_settings_engine():
    db_url = get_config().sqlalchemy_database_uri_settings
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql)
    return engine


EngineName = Literal["audit", "main", "settings"]


@cache_stats()
@lru_cache
def get_session_maker(engine_name: EngineName):
    main_engine = make_main_engine()
    audit_engine = make_audit_engine()
    settings_engine = make_settings_engine()

    engines = {
        "main": main_engine,
        "audit": audit_engine,
        "settings": settings_engine,
    }

    if get_config().print_sql:
        _format = "%(asctime)s.%(msecs)03d : %(levelname)s : %(message)s"
        logging.basicConfig(format=_format, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO, force=True)
        sqlalchemy_pretty_printer.setup(format=_format)
    selected_engine = engines[engine_name]
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=selected_engine)
    return SessionLocal


@contextmanager
def session_scope():
    session_maker = get_session_maker("main")
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_audit_scope():
    session_maker = get_session_maker("audit")
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_settings_scope():
    session_maker = get_session_maker("settings")
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
