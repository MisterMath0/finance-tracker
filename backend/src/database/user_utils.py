# backend/src/database/user_utils.py
from sqlalchemy.orm import Session
from .models import User
from typing import Optional
import bcrypt

class UserManager:
    @staticmethod
    def create_test_user(db: Session) -> User:
        """Create a test user if it doesn't exist."""
        # Check if test user exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            # Create hashed password
            hashed_password = bcrypt.hashpw("testpassword".encode('utf-8'), bcrypt.gensalt())
            
            # Create new test user
            test_user = User(
                email="test@example.com",
                hashed_password=hashed_password.decode('utf-8')
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        return test_user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    