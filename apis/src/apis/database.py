import logging

from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apis.config.current import get_config
from apis.utils import sqlalchemy_pretty_printer
from services.utilities.observability import cache_stats


@cache_stats()
@lru_cache
def get_sesion_maker(db_url: str):
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql)
    if get_config().print_sql:
        _format = "%(asctime)s.%(msecs)03d : %(levelname)s : %(message)s"
        logging.basicConfig(format=_format, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO, force=True)
        sqlalchemy_pretty_printer.setup(format=_format)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def get_session():
    db_url = get_config().sqlalchemy_database_uri
    session_maker = get_sesion_maker(db_url)
    session = session_maker()
    try:
        yield session
    finally:
        session.close()
