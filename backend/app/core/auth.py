"""
Authentication & Authorization Module
JWT-based authentication with role-based access control
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Security configs from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nexus-risk-platform-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
API_KEY = os.getenv("API_KEY", "nexus-api-key-change-in-production")

# Password hashing - using bcrypt
import bcrypt

def _hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ==================== MODELS ====================

class TokenData(BaseModel):
    user_id: str
    email: str
    roles: List[str] = []
    exp: Optional[datetime] = None


class User(BaseModel):
    id: str
    email: str
    name: str
    roles: List[str] = ["viewer"]  # viewer, operator, admin
    is_active: bool = True


class UserInDB(User):
    hashed_password: str


# ==================== MOCK USER DATABASE ====================
# In production, replace with actual Supabase user queries
# Passwords are properly hashed with bcrypt (cost factor 12)

MOCK_USERS = {
    "admin@nexus.io": UserInDB(
        id="usr_001",
        email="admin@nexus.io",
        name="Admin User",
        roles=["admin", "operator", "viewer"],
        is_active=True,
        # password: admin123
        hashed_password="$2b$12$To73XWEULIFUdibY8TMZIOJKqm2RjMLioe.9jf.mEjB71DOR4.Otq"
    ),
    "operator@nexus.io": UserInDB(
        id="usr_002",
        email="operator@nexus.io",
        name="Fleet Operator",
        roles=["operator", "viewer"],
        is_active=True,
        # password: operator123
        hashed_password="$2b$12$Bef235fevrh.BqBUf9H03eMSic8IyLQ4H/IMFENICjNFT/nxgGDbO"
    ),
    "viewer@nexus.io": UserInDB(
        id="usr_003",
        email="viewer@nexus.io",
        name="Viewer User",
        roles=["viewer"],
        is_active=True,
        # password: viewer123
        hashed_password="$2b$12$JansfDiyLL36Q.ONjSIHOuZpV5KuOLWSfHEVD/Yr2fczsFAILIKZO"
    ),
}


# ==================== HELPER FUNCTIONS ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    return _verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return _hash_password(password)


def get_user(email: str) -> Optional[UserInDB]:
    return MOCK_USERS.get(email)


def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload.get("exp", 0))
        )
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


# ==================== DEPENDENCY FUNCTIONS ====================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> User:
    """
    Validate JWT token and return current user.
    Used as a dependency on protected endpoints.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user(token_data.email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        roles=user.roles,
        is_active=user.is_active
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Optional[User]:
    """
    Optional authentication - returns None if no token provided.
    Useful for endpoints that work differently for authenticated users.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> bool:
    """
    Verify API key for service-to-service communication.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return True


# ==================== ROLE-BASED ACCESS CONTROL ====================

class RoleChecker:
    """
    Dependency class for role-based access control.
    Usage: Depends(RoleChecker(["admin", "operator"]))
    """
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        # Check if user has any of the required roles
        if not any(role in user.roles for role in self.required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {self.required_roles}",
            )
        return user


# Convenience dependencies for common role checks
require_admin = RoleChecker(["admin"])
require_operator = RoleChecker(["admin", "operator"])
require_viewer = RoleChecker(["admin", "operator", "viewer"])


# ==================== HELPER FOR LOGGING ACCESS ====================

def log_access(user: User, action: str, resource: str):
    """Log user access for audit trail"""
    logger.info(f"ACCESS: user={user.email} action={action} resource={resource}")
