# backend/src/api/dependencies.py
from typing import Generator
from sqlalchemy.orm import Session
from database.config import get_db

# Re-export the database dependency
def get_database() -> Generator[Session, None, None]:
    db = None
    try:
        db = next(get_db())
        yield db
    finally:
        if db:
            db.close()