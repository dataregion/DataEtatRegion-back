from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apis.config.current import config


db_url = config.sqlalchemy_database_uri
engine = create_engine(
    db_url, pool_pre_ping=True, pool_recycle=30, echo=config.print_sql
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
