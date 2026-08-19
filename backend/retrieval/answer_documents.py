"""Load an explicitly configured general-purpose answer corpus."""

from __future__ import annotations

import json
from pathlib import Path

from .retrieve import Document


def load_answer_documents(corpus_path: str | Path) -> list[Document]:
    """Load trusted answer documents; missing configuration means no corpus."""

    path = Path(corpus_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configured answer corpus was not found: {path}")

    documents: list[Document] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid answer corpus JSON at line {line_number}.") from exc

            title = record.get("title")
            content = record.get("content")
            source = record.get("source")
            url = record.get("url")
            if isinstance(title, str) and isinstance(content, str) and isinstance(source, str):
                documents.append(Document(title=title, content=content, source=source, url=url if isinstance(url, str) else None))

    if not documents:
        raise ValueError(f"No valid answer documents were found in {path}.")
    return documents