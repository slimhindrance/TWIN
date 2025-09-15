"""
User models and authentication schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    PREMIUM = "premium"


class User(BaseModel):
    """User model."""
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username for display")
    role: UserRole = Field(UserRole.USER, description="User role")
    is_active: bool = Field(True, description="Whether user account is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    subscription_tier: str = Field("free", description="Subscription tier")
    usage_count: int = Field(0, description="Number of API calls made")
    monthly_limit: int = Field(100, description="Monthly usage limit")


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username for display")
    password: str = Field(..., min_length=8, description="User password")


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """User response schema (without sensitive data)."""
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    subscription_tier: str
    usage_count: int
    monthly_limit: int


class Token(BaseModel):
    """JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    subscription_tier: Optional[str] = None
    monthly_limit: Optional[int] = None


class UserUsageUpdate(BaseModel):
    """Update user usage count."""
    increment: int = Field(1, description="Amount to increment usage by")
