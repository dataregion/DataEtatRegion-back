from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # Adjust to your ORM base path

DATABASE_URL = "sqlite:///./tests/test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional: expose original dependency to override it in app
get_test_db.original_dep = "your.path.to.get_db"