from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from apis.config import config


db_url = config["SQLALCHEMY_DATABASE_URI"]
engine = create_engine(
    db_url, pool_pre_ping=True, pool_recycle=30, echo=config["PRINT_SQL"]
)
SessionLocal: Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
