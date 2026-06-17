"""
BIRD Backend Security Module

Handles password hashing, JWT token generation, and authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from config.settings import get_settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()


class TokenData(BaseModel):
    """Token data model."""
    user_id: str
    username: str
    exp: datetime


class PasswordHasher:
    """Password hashing utilities."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)


class TokenManager:
    """JWT token management utilities."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time delta
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            
            user_id: str = payload.get("user_id")
            username: str = payload.get("username")
            
            if user_id is None or username is None:
                return None
            
            return TokenData(
                user_id=user_id,
                username=username,
                exp=datetime.fromtimestamp(payload.get("exp"))
            )
        
        except JWTError:
            return None


class SessionManager:
    """Session management utilities."""
    
    @staticmethod
    def create_session_token() -> str:
        """
        Create a secure session token.
        
        Returns:
            Session token string
        """
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_session_expired(expires_at: datetime) -> bool:
        """
        Check if a session has expired.
        
        Args:
            expires_at: Session expiration datetime
            
        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > expires_at


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return PasswordHasher.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return PasswordHasher.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token."""
    return TokenManager.create_access_token(data, expires_delta)


def verify_token(token: str) -> Optional[TokenData]:
    """Verify a token."""
    return TokenManager.verify_token(token)


def create_session_token() -> str:
    """Create a session token."""
    return SessionManager.create_session_token()


def is_session_expired(expires_at: datetime) -> bool:
    """Check if a session is expired."""
    return SessionManager.is_session_expired(expires_at)
