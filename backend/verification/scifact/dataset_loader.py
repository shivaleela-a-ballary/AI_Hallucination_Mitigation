"""Local-only loader for an official SciFact dataset export."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


class SciFactResourceError(FileNotFoundError):
    """Raised when a required local SciFact resource is unavailable."""


@dataclass(frozen=True)
class SciFactDatasetPaths:
    """Locations expected in a local SciFact dataset export."""

    root: Path
    corpus: Path
    claims_train: Path
    claims_dev: Path
    claims_test: Path


class SciFactDatasetLoader:
    """Discover and read local JSONL SciFact resources without downloading them."""

    def __init__(self, dataset_root: str | Path) -> None:
        self.root = Path(dataset_root).expanduser().resolve()

    def paths(self) -> SciFactDatasetPaths:
        return SciFactDatasetPaths(
            root=self.root,
            corpus=self.root / "corpus.jsonl",
            claims_train=self.root / "claims_train.jsonl",
            claims_dev=self.root / "claims_dev.jsonl",
            claims_test=self.root / "claims_test.jsonl",
        )

    def validate(self, require_all_splits: bool = False) -> SciFactDatasetPaths:
        """Validate the local layout and raise a clear error when it is absent."""
        paths = self.paths()
        required = [paths.corpus, paths.claims_train]
        if require_all_splits:
            required.extend([paths.claims_dev, paths.claims_test])
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise SciFactResourceError(
                "SciFact resources are not available locally. Missing: " + ", ".join(missing)
            )
        return paths

    def load_corpus(self) -> dict[int, dict[str, Any]]:
        """Load the local corpus keyed by its integer document identifier."""
        paths = self.validate()
        documents: dict[int, dict[str, Any]] = {}
        for record in self._read_jsonl(paths.corpus):
            if "doc_id" not in record:
                raise ValueError("A SciFact corpus record is missing 'doc_id'.")
            documents[int(record["doc_id"])] = record
        return documents

    def load_claims(self, split: str) -> list[dict[str, Any]]:
        """Load a named local split: ``train``, ``dev``, or ``test``."""
        paths = self.paths()
        split_paths = {"train": paths.claims_train, "dev": paths.claims_dev, "test": paths.claims_test}
        if split not in split_paths:
            raise ValueError("split must be one of: train, dev, test.")
        path = split_paths[split]
        if not path.is_file():
            raise SciFactResourceError(f"SciFact {split} split is not available locally: {path}")
        return list(self._read_jsonl(path))

    @staticmethod
    def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL in {path} at line {line_number}.") from exc
                if not isinstance(record, dict):
                    raise ValueError(f"Expected an object in {path} at line {line_number}.")
                yield record
