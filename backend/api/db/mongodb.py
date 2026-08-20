"""
MongoDB Atlas database client and collections management.
Provides connection pooling, automated index creation, and fallback in-memory store.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pymongo
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from api.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MongoDB Atlas connections and handles three core collections:
    - users
    - verification_history
    - user_settings
    """

    def __init__(self) -> None:
        self.client: Optional[pymongo.MongoClient] = None
        self.db: Optional[Database] = None
        self._connected: bool = False
        self._lock = RLock()

        # In-memory storage fallback
        self._memory_users: Dict[str, dict] = {}
        self._memory_settings: Dict[str, dict] = {}
        self._memory_history: List[dict] = []

    def connect(self) -> bool:
        """Attempt to connect to MongoDB Atlas or local MongoDB."""
        uri = settings.MONGODB_URI
        if not uri:
            logger.info("MONGODB_URI not configured. Operating in fallback in-memory store mode.")
            self._connected = False
            return False

        with self._lock:
            try:
                self.client = pymongo.MongoClient(
                    uri,
                    serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
                    connectTimeoutMS=settings.MONGODB_TIMEOUT_MS,
                    appName="AIHallucinationMitigation",
                )
                # Verify connection with ping
                self.client.admin.command("ping")
                self.db = self.client[settings.MONGODB_DB_NAME]
                self._connected = True
                logger.info(
                    "Connected to MongoDB successfully. Database: '%s'",
                    settings.MONGODB_DB_NAME,
                )
                self._ensure_indexes()
                return True
            except (PyMongoError, Exception) as exc:
                logger.warning(
                    "Could not connect to MongoDB (%s). Falling back to memory store: %s",
                    type(exc).__name__,
                    exc,
                )
                self._connected = False
                self.client = None
                self.db = None
                return False

    def close(self) -> None:
        """Close MongoDB connection gracefully."""
        with self._lock:
            if self.client:
                try:
                    self.client.close()
                except Exception as exc:
                    logger.warning("Error closing MongoDB client: %s", exc)
                finally:
                    self.client = None
                    self.db = None
                    self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.db is not None

    def _ensure_indexes(self) -> None:
        """Create indexes on users, user_settings, and verification_history collections."""
        if not self.is_connected or self.db is None:
            return
        try:
            # users collection
            users_col: Collection = self.db["users"]
            users_col.create_index("email", unique=True, sparse=True)
            users_col.create_index("username", unique=True, sparse=True)

            # user_settings collection
            settings_col: Collection = self.db["user_settings"]
            settings_col.create_index("user_id", unique=True)

            # verification_history collection
            history_col: Collection = self.db["verification_history"]
            history_col.create_index([("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
            history_col.create_index("id", unique=True)
            logger.info("MongoDB indexes verified successfully.")
        except Exception as exc:
            logger.warning("Failed to create MongoDB indexes: %s", exc)

    # -------------------------------------------------------------------------
    # Users Collection Operations
    # -------------------------------------------------------------------------

    def create_user(self, user_data: dict) -> dict:
        user = dict(user_data)
        if "id" not in user:
            user["id"] = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        user.setdefault("created_at", now)
        user.setdefault("updated_at", now)

        if self.is_connected and self.db is not None:
            try:
                self.db["users"].insert_one(dict(user))
                user.pop("_id", None)
                return user
            except Exception as exc:
                logger.error("MongoDB create_user error: %s", exc)
                raise

        with self._lock:
            self._memory_users[user["id"]] = dict(user)
        return user

    def find_user_by_id(self, user_id: str) -> Optional[dict]:
        if not user_id:
            return None
        if self.is_connected and self.db is not None:
            try:
                doc = self.db["users"].find_one({"id": user_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.error("MongoDB find_user_by_id error: %s", exc)

        with self._lock:
            user = self._memory_users.get(user_id)
            return dict(user) if user else None

    def find_user_by_email(self, email: str) -> Optional[dict]:
        if not email:
            return None
        normalized = email.strip().lower()
        if self.is_connected and self.db is not None:
            try:
                doc = self.db["users"].find_one({"email": normalized})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.error("MongoDB find_user_by_email error: %s", exc)

        with self._lock:
            for user in self._memory_users.values():
                if user.get("email", "").strip().lower() == normalized:
                    return dict(user)
            return None

    def find_user_by_username(self, username: str) -> Optional[dict]:
        if not username:
            return None
        normalized = username.strip().lower()
        if self.is_connected and self.db is not None:
            try:
                doc = self.db["users"].find_one({"username": normalized})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.error("MongoDB find_user_by_username error: %s", exc)

        with self._lock:
            for user in self._memory_users.values():
                if user.get("username", "").strip().lower() == normalized:
                    return dict(user)
            return None

    def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        updates = dict(updates)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        updates.pop("_id", None)
        updates.pop("id", None)

        if self.is_connected and self.db is not None:
            try:
                self.db["users"].update_one({"id": user_id}, {"$set": updates})
                return self.find_user_by_id(user_id)
            except Exception as exc:
                logger.error("MongoDB update_user error: %s", exc)

        with self._lock:
            if user_id in self._memory_users:
                self._memory_users[user_id].update(updates)
                return dict(self._memory_users[user_id])
            return None

    # -------------------------------------------------------------------------
    # User Settings Collection Operations
    # -------------------------------------------------------------------------

    def get_user_settings(self, user_id: str) -> dict:
        default_settings = {
            "id": str(uuid4()),
            "user_id": user_id,
            "theme": "dark",
            "default_min_similarity": 0.45,
            "default_top_k": 5,
            "preferred_model": "sentence-transformers/all-MiniLM-L6-v2",
            "auto_save_history": True,
            "email_notifications": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if not user_id:
            return default_settings

        if self.is_connected and self.db is not None:
            try:
                doc = self.db["user_settings"].find_one({"user_id": user_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
                # If not found, insert default settings
                self.db["user_settings"].insert_one(dict(default_settings))
                return default_settings
            except Exception as exc:
                logger.error("MongoDB get_user_settings error: %s", exc)

        with self._lock:
            if user_id not in self._memory_settings:
                self._memory_settings[user_id] = dict(default_settings)
            return dict(self._memory_settings[user_id])

    def update_user_settings(self, user_id: str, updates: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        clean_updates = dict(updates)
        clean_updates.pop("_id", None)
        clean_updates.pop("id", None)
        clean_updates.pop("user_id", None)
        clean_updates["updated_at"] = now

        if self.is_connected and self.db is not None:
            try:
                self.db["user_settings"].update_one(
                    {"user_id": user_id},
                    {"$set": clean_updates},
                    upsert=True,
                )
                return self.get_user_settings(user_id)
            except Exception as exc:
                logger.error("MongoDB update_user_settings error: %s", exc)

        with self._lock:
            current = self.get_user_settings(user_id)
            current.update(clean_updates)
            self._memory_settings[user_id] = current
            return dict(current)

    # -------------------------------------------------------------------------
    # Verification History Collection Operations
    # -------------------------------------------------------------------------

    def add_verification_history(
        self,
        record: dict,
        user_id: Optional[str] = None,
    ) -> dict:
        item = dict(record)
        if "id" not in item or not item["id"]:
            item["id"] = str(uuid4())
        if "created_at" not in item or not item["created_at"]:
            item["created_at"] = datetime.now(timezone.utc).isoformat()
        item["user_id"] = user_id

        if self.is_connected and self.db is not None:
            try:
                self.db["verification_history"].insert_one(dict(item))
                item.pop("_id", None)
                return item
            except Exception as exc:
                logger.error("MongoDB add_verification_history error: %s", exc)

        with self._lock:
            self._memory_history.insert(0, dict(item))
        return item

    def get_user_verification_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        if self.is_connected and self.db is not None:
            try:
                query: Dict[str, Any] = {}
                if user_id:
                    # Return items created by this user OR general guest items if none
                    query = {"$or": [{"user_id": user_id}, {"user_id": None}]}
                cursor = self.db["verification_history"].find(query).sort("created_at", pymongo.DESCENDING).limit(limit)
                items = []
                for doc in cursor:
                    doc.pop("_id", None)
                    items.append(doc)
                return items
            except Exception as exc:
                logger.error("MongoDB get_user_verification_history error: %s", exc)

        with self._lock:
            if user_id:
                filtered = [
                    dict(h)
                    for h in self._memory_history
                    if h.get("user_id") == user_id or h.get("user_id") is None
                ]
                return filtered[:limit]
            return [dict(h) for h in self._memory_history[:limit]]

    def get_history_item(self, item_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        if not item_id:
            return None
        if self.is_connected and self.db is not None:
            try:
                doc = self.db["verification_history"].find_one({"id": item_id})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as exc:
                logger.error("MongoDB get_history_item error: %s", exc)

        with self._lock:
            for item in self._memory_history:
                if item.get("id") == item_id:
                    return dict(item)
            return None

    def delete_history_item(self, item_id: str, user_id: Optional[str] = None) -> bool:
        if not item_id:
            return False
        if self.is_connected and self.db is not None:
            try:
                query: Dict[str, Any] = {"id": item_id}
                if user_id:
                    query["$or"] = [{"user_id": user_id}, {"user_id": None}]
                result = self.db["verification_history"].delete_one(query)
                return result.deleted_count > 0
            except Exception as exc:
                logger.error("MongoDB delete_history_item error: %s", exc)

        with self._lock:
            for idx, item in enumerate(self._memory_history):
                if item.get("id") == item_id:
                    if user_id and item.get("user_id") not in (user_id, None):
                        return False
                    self._memory_history.pop(idx)
                    return True
            return False

    def clear_user_history(self, user_id: Optional[str] = None) -> int:
        if self.is_connected and self.db is not None:
            try:
                query: Dict[str, Any] = {"user_id": user_id} if user_id else {}
                result = self.db["verification_history"].delete_many(query)
                return result.deleted_count
            except Exception as exc:
                logger.error("MongoDB clear_user_history error: %s", exc)

        with self._lock:
            count = 0
            new_history = []
            for item in self._memory_history:
                if user_id and item.get("user_id") == user_id:
                    count += 1
                elif not user_id:
                    count += 1
                else:
                    new_history.append(item)
            self._memory_history = new_history
            return count

    def get_stats(self) -> dict:
        """Returns statistics on MongoDB connectivity and collection counts."""
        connected = self.is_connected
        stats = {
            "connected": connected,
            "storage_mode": "MongoDB Atlas" if connected else "In-Memory Fallback",
            "database_name": settings.MONGODB_DB_NAME if connected else "in_memory",
            "users_count": 0,
            "history_count": 0,
            "settings_count": 0,
        }
        if connected and self.db is not None:
            try:
                stats["users_count"] = self.db["users"].count_documents({})
                stats["history_count"] = self.db["verification_history"].count_documents({})
                stats["settings_count"] = self.db["user_settings"].count_documents({})
            except Exception as exc:
                logger.warning("Error fetching MongoDB counts: %s", exc)
        else:
            stats["users_count"] = len(self._memory_users)
            stats["history_count"] = len(self._memory_history)
            stats["settings_count"] = len(self._memory_settings)
        return stats


db_manager = DatabaseManager()
