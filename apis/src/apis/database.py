from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apis.config.current import get_config


@lru_cache
def get_sesion_maker(db_url: str):
    engine = create_engine(
        db_url, pool_pre_ping=True, pool_recycle=30, echo=get_config().print_sql
    )
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
