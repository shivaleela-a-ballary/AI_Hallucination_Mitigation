"""
Health check endpoint reporting real status of all internal and external subsystems.
"""

from __future__ import annotations

import urllib.request
from fastapi import APIRouter
from api.config import settings
from api.db.mongodb import db_manager

router = APIRouter(tags=["Health"])


def _check_http_endpoint(url: str, timeout: float = 2.0) -> bool:
    """Quick non-blocking connectivity probe."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AIHallucinationMitigation/HealthCheck"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 204, 301, 302)
    except Exception:
        return False


@router.get("/health")
def health_check():
    corpus_available = settings.SCIFACT_CORPUS_PATH.is_file()
    model_available = settings.SCIFACT_MODEL_PATH.is_dir()
    faiss_available = (settings.PROJECT_ROOT / "data" / "scifact" / "cache" / "index.faiss").is_file()
    db_stats = db_manager.get_stats()

    # External provider connectivity probes (short 2s timeout)
    pubmed_online = _check_http_endpoint("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=health&retmode=json&retmax=1", timeout=2.5) if settings.PUBMED_ENABLED else False
    wikipedia_online = _check_http_endpoint("https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&format=json", timeout=2.5) if settings.WIKIPEDIA_ENABLED else False

    is_healthy = corpus_available or faiss_available

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": "AI Hallucination Mitigation API",
        "version": settings.APP_VERSION,
        "scifact_corpus_available": corpus_available,
        "scifact_model_available": model_available,
        "faiss_index_available": faiss_available,
        "mongodb_connected": db_stats["connected"],
        "mongodb_mode": db_stats["storage_mode"],
        "database_name": db_stats["database_name"],
        "pubmed_available": pubmed_online,
        "wikipedia_available": wikipedia_online,
        "subsystems": {
            "scibert": "✓ Available" if model_available else "ℹ Baseline Mode",
            "scifact": "✓ Available" if corpus_available else "⚠ Missing Corpus",
            "faiss": "✓ Indexed" if faiss_available else "ℹ In-Memory",
            "mongodb": "✓ Connected" if db_stats["connected"] else "ℹ In-Memory Fallback",
            "pubmed": "✓ Available" if pubmed_online else "⚠ Unavailable",
            "wikipedia": "✓ Available" if wikipedia_online else "⚠ Unavailable",
        },
        "stats": db_stats,
    }
