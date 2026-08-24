"""Small in-memory store for results produced by this API process."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4


class HistoryStore:
    def __init__(self) -> None:
        self._items: list[dict] = []
        self._lock = Lock()

    def add(self, query: str, result: dict) -> dict:
        item = {"id": str(uuid4()), "query": query, "created_at": datetime.now(timezone.utc).isoformat(), **result}
        with self._lock:
            self._items.insert(0, item)
        return item

    def list(self) -> list[dict]:
        with self._lock:
            return list(self._items)

    def get(self, item_id: str) -> dict | None:
        with self._lock:
            return next((item for item in self._items if item.get("id") == item_id), None)

    def delete(self, item_id: str) -> bool:
        with self._lock:
            initial_len = len(self._items)
            self._items = [item for item in self._items if item.get("id") != item_id]
            return len(self._items) < initial_len

    def clear(self) -> int:
        with self._lock:
            count = len(self._items)
            self._items.clear()
            return count


history_store = HistoryStore()
