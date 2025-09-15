"""
Authentication endpoints
"""
import logging
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.user import User, UserCreate, UserLogin, Token, UserResponse, UserUpdate
from app.core.auth import AuthService, get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    try:
        # Create user
        user = AuthService.create_user(user_data)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        logger.info(f"New user registered: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user.dict())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin):
    """Login user."""
    try:
        # Authenticate user
        user = AuthService.authenticate_user(user_data.email, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer", 
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user.dict())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(**current_user.dict())


@router.put("/me", response_model=UserResponse) 
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user information."""
    try:
        # Update user (in production, update in database)
        from app.core.auth import users_db
        
        user_data = users_db.get(current_user.id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = User(**user_data["user"])
        
        # Update fields
        if user_update.username is not None:
            user.username = user_update.username
        if user_update.subscription_tier is not None:
            user.subscription_tier = user_update.subscription_tier
        if user_update.monthly_limit is not None:
            user.monthly_limit = user_update.monthly_limit
            
        # Save updated user
        users_db[current_user.id]["user"] = user.dict()
        
        logger.info(f"User updated: {user.email}")
        
        return UserResponse(**user.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.get("/usage", response_model=dict)
async def get_user_usage(current_user: User = Depends(get_current_user)):
    """Get current user usage statistics."""
    return {
        "usage_count": current_user.usage_count,
        "monthly_limit": current_user.monthly_limit,
        "remaining": current_user.monthly_limit - current_user.usage_count,
        "percentage_used": (current_user.usage_count / current_user.monthly_limit) * 100,
        "subscription_tier": current_user.subscription_tier
    }


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """Logout user (client should delete token)."""
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}
