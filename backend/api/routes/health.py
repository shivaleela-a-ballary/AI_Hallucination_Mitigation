from fastapi import APIRouter
from api.config import settings
from api.db.mongodb import db_manager

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    corpus_available = settings.SCIFACT_CORPUS_PATH.is_file()
    model_available = settings.SCIFACT_MODEL_PATH.is_dir()
    db_stats = db_manager.get_stats()

    return {
        "status": "healthy" if corpus_available and model_available else "degraded",
        "service": "AI Hallucination Mitigation API",
        "scifact_corpus_available": corpus_available,
        "scifact_model_available": model_available,
        "mongodb_connected": db_stats["connected"],
        "mongodb_mode": db_stats["storage_mode"],
        "database_name": db_stats["database_name"],
        "stats": db_stats,
    }

