"""
Authentication management
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.database import User, SessionLocal, init_database
from app.core.config import settings

class AuthManager:
    """Handles user authentication"""
    
    def __init__(self):
        init_database()
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_token(self, user_id: int) -> str:
        """Create JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=settings.TOKEN_EXPIRE_HOURS)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def register(self, username: str, password: str) -> Tuple[bool, str]:
        """Register a new user"""
        db = SessionLocal()
        
        try:
            # Check if user exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "Username already exists"
            
            # Create user
            password_hash = self.hash_password(password)
            user = User(username=username, password_hash=password_hash)
            db.add(user)
            db.commit()
            
            return True, "User registered successfully"
            
        except Exception as e:
            db.rollback()
            return False, f"Registration failed: {str(e)}"
        finally:
            db.close()
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        db = SessionLocal()
        
        try:
            user = db.query(User).filter(User.username == username).first()
            
            if user and self.verify_password(password, user.password_hash):
                # Update last login
                user.last_login = datetime.utcnow()
                db.commit()
                return user
            
            return None
            
        finally:
            db.close()
    
    def is_first_boot(self) -> bool:
        """Check if this is the first boot (no users exist)"""
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            return user_count == 0
        finally:
            db.close()