from fastapi import APIRouter, Depends, HTTPException

from api.db.mongodb import db_manager
from api.dependencies import get_optional_current_user
from api.services.history_store import history_store

router = APIRouter(tags=["History"])


@router.get("/history")
def history(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    items = db_manager.get_user_verification_history(user_id=user_id, limit=100)
    if not items:
        items = history_store.list()
    return {"history": items}


@router.get("/history/{item_id}")
def history_item(
    item_id: str,
    current_user: dict | None = Depends(get_optional_current_user),
):
    user_id = current_user.get("id") if current_user else None
    item = db_manager.get_history_item(item_id, user_id=user_id)
    if item is None:
        item = history_store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Verification record not found")
    return item


@router.get("/graph/latest")
def latest_graph(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    items = db_manager.get_user_verification_history(user_id=user_id, limit=1)
    if not items:
        items = history_store.list()
    if not items:
        return {"nodes": [], "edges": []}
    return items[0].get("knowledge_graph", {"nodes": [], "edges": []})


@router.get("/graph/{item_id}")
def graph_for_answer(
    item_id: str,
    current_user: dict | None = Depends(get_optional_current_user),
):
    user_id = current_user.get("id") if current_user else None
    item = db_manager.get_history_item(item_id, user_id=user_id)
    if item is None:
        item = history_store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return item.get("knowledge_graph", {"nodes": [], "edges": []})

