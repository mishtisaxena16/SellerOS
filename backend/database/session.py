from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from backend.database.database import engine


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """
    FastAPI database dependency.

    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()