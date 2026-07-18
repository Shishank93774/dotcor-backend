from app.core.config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
