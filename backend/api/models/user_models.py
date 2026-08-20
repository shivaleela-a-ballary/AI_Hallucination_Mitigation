"""
User profile and user settings Pydantic models.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class UserProfileUpdateRequest(BaseModel):
    """Payload to update user profile information."""
    full_name: Optional[str] = Field(default=None, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=500)
    avatar_url: Optional[str] = Field(default=None, max_length=1000)


class UserSettingsModel(BaseModel):
    """User preferences stored in user_settings collection."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    theme: str = Field(default="dark", description="'dark' or 'light'")
    default_min_similarity: float = Field(default=0.45, ge=0.0, le=1.0)
    default_top_k: int = Field(default=5, ge=1, le=20)
    preferred_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    auto_save_history: bool = Field(default=True)
    email_notifications: bool = Field(default=True)
    updated_at: Optional[str] = None


class UserSettingsUpdateRequest(BaseModel):
    """Payload to update user settings."""
    theme: Optional[str] = Field(default=None)
    default_min_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    default_top_k: Optional[int] = Field(default=None, ge=1, le=20)
    preferred_model: Optional[str] = Field(default=None)
    auto_save_history: Optional[bool] = Field(default=None)
    email_notifications: Optional[bool] = Field(default=None)
