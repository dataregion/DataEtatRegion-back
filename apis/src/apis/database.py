
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


db_url = "postgresql+psycopg://postgres:passwd@localhost:15432/CHORUS"

engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=30, echo=True)
SessionLocal: Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
