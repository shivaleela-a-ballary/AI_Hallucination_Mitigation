from fastapi import APIRouter, HTTPException
from api.services.history_store import history_store

router = APIRouter(tags=["History"])


@router.get("/history")
def history():
    return {"history": history_store.list()}


@router.get("/history/{item_id}")
def history_item(item_id: str):
    item = history_store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return item


@router.get("/graph/latest")
def latest_graph():
    items = history_store.list()
    if not items:
        return {"nodes": [], "edges": []}
    return items[0].get("knowledge_graph", {"nodes": [], "edges": []})


@router.get("/graph/{item_id}")
def graph_for_answer(item_id: str):
    item = history_store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return item.get("knowledge_graph", {"nodes": [], "edges": []})
