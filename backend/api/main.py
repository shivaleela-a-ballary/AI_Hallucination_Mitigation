"""Entrypoint alias for backend.api.main:app compatibility."""
import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from api.app import app  # noqa: F401
