"""
User Profile, Settings, and User Verification History API routes.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.db.mongodb import db_manager
from api.dependencies import get_current_user
from api.models.auth_models import UserProfileResponse, UserSummary
from api.models.user_models import (
    UserProfileUpdateRequest,
    UserSettingsModel,
    UserSettingsUpdateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(user: dict = Depends(get_current_user)):
    """
    Get full profile and settings for the authenticated user.
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


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """
    Update profile details for the authenticated user.
    """
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated_user = db_manager.update_user(user["id"], updates) or user
    settings_doc = db_manager.get_user_settings(user["id"])

    return UserProfileResponse(
        user=UserSummary(
            id=updated_user["id"],
            username=updated_user["username"],
            email=updated_user["email"],
            full_name=updated_user.get("full_name", ""),
            role=updated_user.get("role", "user"),
            created_at=updated_user.get("created_at"),
        ),
        settings=settings_doc,
    )


@router.get("/settings", response_model=UserSettingsModel)
def get_settings(user: dict = Depends(get_current_user)):
    """
    Retrieve user preferences from user_settings MongoDB collection.
    """
    settings_doc = db_manager.get_user_settings(user["id"])
    return UserSettingsModel(**settings_doc)


@router.put("/settings", response_model=UserSettingsModel)
def update_settings(
    payload: UserSettingsUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """
    Update user preferences in user_settings MongoDB collection.
    """
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    saved_settings = db_manager.update_user_settings(user["id"], updates)
    return UserSettingsModel(**saved_settings)


@router.get("/history")
def get_user_history(
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """
    Fetch verification & chat history from MongoDB for the current user.
    """
    items = db_manager.get_user_verification_history(user_id=user["id"], limit=limit)
    return {"history": items, "count": len(items)}


@router.delete("/history/{item_id}")
def delete_user_history_item(
    item_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Delete a specific verification item from MongoDB history.
    """
    deleted = db_manager.delete_history_item(item_id=item_id, user_id=user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification record not found or not owned by user.",
        )
    return {"message": "History item deleted successfully", "id": item_id}


@router.delete("/history")
def clear_user_history(user: dict = Depends(get_current_user)):
    """
    Clear all verification history in MongoDB for the current user.
    """
    deleted_count = db_manager.clear_user_history(user_id=user["id"])
    return {
        "message": "All verification history cleared.",
        "deleted_count": deleted_count,
    }
