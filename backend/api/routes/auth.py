"""
Authentication routes for User Registration, Login, Profile and JWT issuance.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from api.config import settings
from api.db.mongodb import db_manager
from api.dependencies import get_current_user
from api.models.auth_models import (
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserSummary,
)
from api.security.auth import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest):
    """
    Register a new user account with hashed password,
    creates their default user settings in MongoDB,
    and returns a signed JWT token.
    """
    email_clean = payload.email.strip().lower()
    username_clean = payload.username.strip().lower()

    # Check for existing email
    if db_manager.find_user_by_email(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Check for existing username
    if db_manager.find_user_by_username(username_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken. Please choose another.",
        )

    user_id = str(uuid4())
    hashed = hash_password(payload.password)

    user_doc = {
        "id": user_id,
        "username": username_clean,
        "email": email_clean,
        "full_name": payload.full_name.strip() if payload.full_name else username_clean,
        "hashed_password": hashed,
        "role": "user",
        "bio": "",
        "avatar_url": "",
    }

    created_user = db_manager.create_user(user_doc)

    # Initialize default user settings in MongoDB user_settings collection
    db_manager.get_user_settings(user_id)

    # Create JWT Access Token
    access_token = create_access_token(
        data={"sub": user_id, "username": username_clean, "email": email_clean}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary(
            id=created_user["id"],
            username=created_user["username"],
            email=created_user["email"],
            full_name=created_user.get("full_name", ""),
            role=created_user.get("role", "user"),
            created_at=created_user.get("created_at"),
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest):
    """
    Authenticate with username or email and password.
    Returns signed JWT access token and user profile summary.
    """
    identifier = payload.username.strip().lower()

    # Attempt find by email first, then username
    user = db_manager.find_user_by_email(identifier) or db_manager.find_user_by_username(identifier)

    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["id"], "username": user["username"], "email": user["email"]}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            role=user.get("role", "user"),
            created_at=user.get("created_at"),
        ),
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Get profile and settings of currently authenticated user.
    """
    settings_doc = db_manager.get_user_settings(user["id"])
    return UserProfileResponse(
        user=UserSummary(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name", ""),
            role=user.get("role", "user"),
            created_at=user.get("created_at"),
        ),
        settings=settings_doc,
    )


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    """
    Logout endpoint to acknowledge client token removal.
    """
    return {"message": "Logged out successfully", "status": "success"}
