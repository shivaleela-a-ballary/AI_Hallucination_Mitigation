"""Load SciFact corpus records into the project's retrieval Document format."""

from __future__ import annotations

import json
from pathlib import Path

from .retrieve import Document


def load_scifact_documents(
    corpus_path: str | Path = "data/scifact/corpus.jsonl",
) -> list[Document]:
    """Load SciFact corpus abstracts as retrieval documents."""

    path = Path(corpus_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"SciFact corpus was not found: {path}"
        )

    documents: list[Document] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in SciFact corpus at line {line_number}."
                ) from exc

            doc_id = record.get("doc_id")
            title = record.get("title")
            abstract = record.get("abstract")

            if doc_id is None or not title or not isinstance(abstract, list):
                continue

            sentences = [
                str(sentence).strip()
                for sentence in abstract
                if str(sentence).strip()
            ]

            if not sentences:
                continue

            documents.append(
                Document(
                    title=str(title),
                    content=" ".join(sentences),
                    source=f"scifact:{doc_id}",
                )
            )

    if not documents:
        raise ValueError(
            f"No valid SciFact documents were found in {path}."
        )

    return documents