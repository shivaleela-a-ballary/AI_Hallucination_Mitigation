from fastapi import APIRouter, Depends, HTTPException

from api.db.mongodb import db_manager
from api.dependencies import get_optional_current_user
from api.services.history_store import history_store

router = APIRouter(tags=["History"])


@router.get("/verification/current")
def current_verification(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    items = db_manager.get_user_verification_history(user_id=user_id, limit=1)
    if not items:
        items = history_store.list()
    if not items:
        raise HTTPException(status_code=404, detail="No verification available. Verify a claim first.")
    return items[0]


@router.get("/history")
def history(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    items = db_manager.get_user_verification_history(user_id=user_id, limit=100)
    if not items:
        items = history_store.list()
    return {"history": items}


@router.delete("/history")
def clear_history(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    deleted_mongo = db_manager.clear_user_history(user_id=user_id)
    deleted_mem = history_store.clear()
    return {
        "message": "All verification history cleared successfully.",
        "deleted_count": deleted_mongo + deleted_mem,
    }


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


@router.delete("/history/{item_id}")
def delete_history_item(
    item_id: str,
    current_user: dict | None = Depends(get_optional_current_user),
):
    user_id = current_user.get("id") if current_user else None
    deleted_mongo = db_manager.delete_history_item(item_id, user_id=user_id)
    deleted_mem = history_store.delete(item_id)
    if not (deleted_mongo or deleted_mem):
        raise HTTPException(status_code=404, detail="Verification record not found")
    return {"message": "Record deleted successfully", "id": item_id}


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


@router.get("/dashboard/stats")
def dashboard_stats(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    try:
        items = db_manager.get_user_verification_history(user_id=user_id, limit=500)
    except Exception:
        items = []
    if not items:
        items = history_store.list()

    total_verifications = len(items)
    total_claims = 0
    supported_claims = 0
    refuted_claims = 0
    uncertain_claims = 0
    hallucinated_verifications = 0
    confidence_sum = 0.0

    risk_distribution = {"low": 0, "moderate": 0, "high": 0}
    pattern_counts = {}
    source_counts = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            raw_conf = item.get("confidence_score") if item.get("confidence_score") is not None else item.get("confidence")
            conf = float(raw_conf) if raw_conf is not None else 0.0
            if conf > 1.0:
                conf = conf / 100.0
            confidence_sum += conf
        except (ValueError, TypeError):
            pass

        status = str(item.get("verification_status") or item.get("status") or item.get("verdict") or "").upper()
        has_hal = bool(item.get("hallucination_detected")) or status in ("REFUTED", "PARTIALLY_VERIFIED")
        if has_hal or status == "REFUTED":
            hallucinated_verifications += 1

        raw_claims = item.get("claims") or []
        if isinstance(raw_claims, list):
            for raw_c in raw_claims:
                if isinstance(raw_c, str):
                    c = {"claim": raw_c, "status": status}
                elif isinstance(raw_c, dict):
                    c = raw_c
                else:
                    continue

                total_claims += 1
                c_status = str(c.get("status") or c.get("verification_status") or c.get("verdict") or "").upper()
                if "SUPPORT" in c_status:
                    supported_claims += 1
                elif "REFUT" in c_status or "CONTRADICT" in c_status:
                    refuted_claims += 1
                else:
                    uncertain_claims += 1

                try:
                    raw_risk = c.get("risk_score")
                    if raw_risk is None:
                        raw_risk = (c.get("hallucination_risk_score") or 0) / 100.0
                    risk = float(raw_risk)
                except (ValueError, TypeError):
                    risk = 0.50 if "REFUT" in c_status else 0.10

                if risk > 0.6:
                    risk_distribution["high"] += 1
                elif risk >= 0.25:
                    risk_distribution["moderate"] += 1
                else:
                    risk_distribution["low"] += 1

                forensics = c.get("forensics") or {}
                if isinstance(forensics, dict):
                    ptype = forensics.get("pattern_type")
                    if ptype and ptype not in ("None / Valid", "None"):
                        pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1

        sources = item.get("sources") or []
        if isinstance(sources, list):
            for s in sources:
                if isinstance(s, dict):
                    stype = s.get("source_type") or "SciFact Knowledge Base"
                    source_counts[stype] = source_counts.get(stype, 0) + 1
                elif isinstance(s, str):
                    source_counts["Literature"] = source_counts.get("Literature", 0) + 1

    avg_confidence = round(confidence_sum / total_verifications, 2) if total_verifications > 0 else None
    hallucination_rate = round((refuted_claims / total_claims) * 100, 1) if total_claims > 0 else (
        round((hallucinated_verifications / total_verifications) * 100, 1) if total_verifications > 0 else None
    )

    top_patterns = [
        {"pattern": k, "count": v}
        for k, v in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    return {
        "total_verifications": total_verifications,
        "total_claims": total_claims,
        "supported_claims": supported_claims,
        "refuted_claims": refuted_claims,
        "uncertain_claims": uncertain_claims,
        "hallucination_rate": hallucination_rate,
        "avg_confidence": avg_confidence,
        "risk_distribution": risk_distribution,
        "top_patterns": top_patterns,
        "source_distribution": source_counts,
        "recent_verifications": items[:10],
    }


@router.get("/sources")
def get_sources(current_user: dict | None = Depends(get_optional_current_user)):
    user_id = current_user.get("id") if current_user else None
    try:
        items = db_manager.get_user_verification_history(user_id=user_id, limit=200)
    except Exception:
        items = []
    if not items:
        items = history_store.list()

    sources_map = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") or item.get("_id")
        created_at = item.get("created_at") or ""
        sources = item.get("sources") or []
        if not isinstance(sources, list):
            continue
        for s in sources:
            if not isinstance(s, dict):
                continue
            name = s.get("title") or s.get("source_name") or s.get("name") or "SciFact Corpus Source"
            key = name.strip()
            if not key:
                continue

            try:
                sim = float(s.get("similarity_score") or s.get("relevance_score") or 0.0)
            except (ValueError, TypeError):
                sim = 0.0
            accepted = bool(s.get("used_as_proof", False)) or s.get("relevance") == "high" or sim >= 0.75

            if key not in sources_map:
                sources_map[key] = {
                    "id": str(s.get("id") or s.get("source_id") or abs(hash(key))),
                    "title": name,
                    "source_type": s.get("source_type") or "SciFact Knowledge Base",
                    "url": s.get("url") or "",
                    "snippets": [s.get("snippet") or s.get("content") or s.get("text") or ""] if (s.get("snippet") or s.get("content") or s.get("text")) else [],
                    "verification_count": 0,
                    "acceptance_status": "ACCEPTED" if accepted else "REFERENCED",
                    "avg_similarity": 0.0,
                    "similarity_sum": 0.0,
                    "latest_used_at": created_at,
                    "referenced_in_records": [],
                }

            rec = sources_map[key]
            rec["verification_count"] += 1
            rec["similarity_sum"] += sim
            rec["avg_similarity"] = round(rec["similarity_sum"] / rec["verification_count"], 3)
            if accepted:
                rec["acceptance_status"] = "ACCEPTED"
            elif rec["acceptance_status"] != "ACCEPTED" and sim < 0.4:
                rec["acceptance_status"] = "REJECTED (Irrelevant)"

            if item_id and item_id not in rec["referenced_in_records"]:
                rec["referenced_in_records"].append(item_id)
            if created_at and (not rec["latest_used_at"] or created_at > rec["latest_used_at"]):
                rec["latest_used_at"] = created_at

    result_sources = list(sources_map.values())
    result_sources.sort(key=lambda x: x["verification_count"], reverse=True)
    return {
        "sources": result_sources,
        "total_sources": len(result_sources),
    }
