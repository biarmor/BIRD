"""
Authentication Router

User registration, login, and token management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, Session as DBSession
from app.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.security import (
    hash_password, verify_password, create_access_token,
    create_session_token, is_session_expired
)
from config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Args:
        request: User registration request
        db: Database session
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Login user and get access token.
    
    Args:
        request: User login request
        db: Database session
        
    Returns:
        Access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )
    
    # Create session
    session_token = create_session_token()
    expires_at = datetime.utcnow() + timedelta(seconds=settings.session_expire_seconds)
    
    db_session = DBSession(
        user_id=user.id,
        token=session_token,
        expires_at=expires_at
    )
    
    db.add(db_session)
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: str, db: Session = Depends(get_db)):
    """
    Logout user and invalidate session.
    
    Args:
        token: Session token
        db: Database session
        
    Returns:
        Logout confirmation
    """
    # Find and delete session
    session = db.query(DBSession).filter(DBSession.token == token).first()
    
    if session:
        db.delete(session)
        db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get current user information.
    
    Args:
        user_id: User ID from token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
