from typing import Dict, Optional
import hashlib
import jwt
import datetime
from pydantic import BaseModel
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

class User(BaseModel):
    """User model"""
    id: str
    username: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False

class UserManager:
    """Manages user authentication and authorization"""
    
    def __init__(self):
        self._users: Dict[str, User] = {}
        
    def create_user(self, username: str, password: str, is_admin: bool = False) -> User:
        """Create new user"""
        if username in self._users:
            raise ValueError(f"User {username} already exists")
            
        user = User(
            id=hashlib.sha256(username.encode()).hexdigest(),
            username=username,
            hashed_password=self._hash_password(password),
            is_admin=is_admin
        )
        self._users[username] = user
        return user
        
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token"""
        user = self._users.get(username)
        if not user or not self._verify_password(password, user.hashed_password):
            return None
            
        return self.create_token(user)
        
    def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"]
            )
            username = payload.get("sub")
            if username is None:
                return None
                
            user = self._users.get(username)
            if user and user.is_active:
                return user
                
        except jwt.InvalidTokenError:
            return None
            
        return None
        
    def create_token(self, user: User) -> str:
        """Create JWT token for user"""
        payload = {
            "sub": user.username,
            "id": user.id,
            "admin": user.is_admin,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(
                minutes=settings.jwt_expire_minutes
            )
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
        
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """Verify password hash"""
        return UserManager._hash_password(password) == hashed

# Global user manager instance
user_manager = UserManager()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """Get current authenticated user from token"""
    user = user_manager.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    return user
