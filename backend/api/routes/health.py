from fastapi import APIRouter
from api.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    corpus_available = settings.SCIFACT_CORPUS_PATH.is_file()
    model_available = settings.SCIFACT_MODEL_PATH.is_dir()
    return {
        "status": "healthy" if corpus_available and model_available else "degraded",
        "service": "AI Hallucination Mitigation API"
        ,"scifact_corpus_available": corpus_available,
        "scifact_model_available": model_available,
    }
