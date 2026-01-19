"""
Authentication API Endpoints
Login, token refresh, and user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.core.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Demo credentials:
    - admin@nexus.io / admin123 (full access)
    - operator@nexus.io / operator123 (fleet operations)
    - viewer@nexus.io / viewer123 (read-only)
    """
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "roles": user.roles
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "roles": user.roles
        }
    )


@router.get("/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles,
        "is_active": user.is_active
    }


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """
    Logout user (client should discard the token).
    In a production system, you might want to blacklist the token.
    """
    return {
        "message": "Logged out successfully",
        "user": user.email
    }


@router.get("/verify")
async def verify_token(user: User = Depends(get_current_user)):
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user_id": user.id,
        "roles": user.roles
    }
