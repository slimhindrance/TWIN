"""
Authentication and authorization utilities
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid

from app.models.user import User, UserCreate, UserRole
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# HTTP Bearer token
security = HTTPBearer()

# In-memory user store (in production, use database)
users_db: Dict[str, Dict[str, Any]] = {}
users_by_email: Dict[str, str] = {}


class AuthService:
    """Authentication service."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    @staticmethod
    def create_user(user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        if user_data.email in users_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Generate user ID
        user_id = str(uuid.uuid4())

        # Create user
        hashed_password = AuthService.hash_password(user_data.password)
        user = User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            subscription_tier="free",
            usage_count=0,
            monthly_limit=100
        )

        # Store user (in production, save to database)
        users_db[user_id] = {
            "user": user.dict(),
            "password_hash": hashed_password
        }
        users_by_email[user_data.email] = user_id

        return user

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user_id = users_by_email.get(email)
        if not user_id:
            return None

        user_data = users_db.get(user_id)
        if not user_data:
            return None

        if not AuthService.verify_password(password, user_data["password_hash"]):
            return None

        # Update last login
        user = User(**user_data["user"])
        user.last_login = datetime.utcnow()
        users_db[user_id]["user"] = user.dict()

        return user

    @staticmethod
    def get_user(user_id: str) -> Optional[User]:
        """Get user by ID."""
        user_data = users_db.get(user_id)
        if not user_data:
            return None
        return User(**user_data["user"])

    @staticmethod
    def update_user_usage(user_id: str, increment: int = 1) -> Optional[User]:
        """Update user usage count."""
        user_data = users_db.get(user_id)
        if not user_data:
            return None

        user = User(**user_data["user"])
        user.usage_count += increment
        users_db[user_id]["user"] = user.dict()

        return user

    @staticmethod
    def check_usage_limit(user: User) -> bool:
        """Check if user has exceeded usage limit."""
        return user.usage_count < user.monthly_limit


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = AuthService.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = AuthService.get_user(user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user with usage limit check."""
    if not AuthService.check_usage_limit(current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly usage limit ({current_user.monthly_limit}) exceeded"
        )
    
    return current_user


# Optional dependency for endpoints that don't require auth
async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get user if authenticated, None otherwise."""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
