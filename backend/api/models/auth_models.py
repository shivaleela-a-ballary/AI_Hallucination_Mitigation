"""
Authentication request and response Pydantic models.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration payload."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(default="", max_length=100)


class UserLoginRequest(BaseModel):
    """User login payload (accepts username or email)."""
    username: str = Field(..., min_length=1, description="Username or email address")
    password: str = Field(..., min_length=1)


class UserSummary(BaseModel):
    """Public user summary."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = ""
    role: Optional[str] = "user"
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT authorization token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class UserProfileResponse(BaseModel):
    """Full user profile response with user settings."""
    user: UserSummary
    settings: Optional[dict] = None
