"""Convert local SciFact annotations into three-way NLI training examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .labels import VerificationLabel


_LABEL_MAP = {
    "SUPPORT": VerificationLabel.SUPPORTED,
    "SUPPORTED": VerificationLabel.SUPPORTED,
    "CONTRADICT": VerificationLabel.REFUTED,
    "REFUTED": VerificationLabel.REFUTED,
    "NEI": VerificationLabel.UNCERTAIN,
    "NOT_ENOUGH_INFO": VerificationLabel.UNCERTAIN,
    "UNCERTAIN": VerificationLabel.UNCERTAIN,
}


@dataclass(frozen=True)
class SciFactExample:
    """A claim/passage pair and its verified SciFact supervision label."""

    claim_id: int
    claim: str
    evidence: str
    label: VerificationLabel
    document_id: int
    rationale_sentence_ids: tuple[int, ...]


class SciFactPreprocessor:
    """Build examples only from supplied official SciFact annotations."""

    def build_examples(
        self,
        claims: Iterable[Mapping[str, Any]],
        corpus: Mapping[int, Mapping[str, Any]],
    ) -> list[SciFactExample]:
        examples: list[SciFactExample] = []
        for claim_record in claims:
            claim_id = int(claim_record["id"])
            claim_text = self._require_text(claim_record, "claim")
            evidence_map = claim_record.get("evidence", {})
            if not isinstance(evidence_map, Mapping):
                raise ValueError(f"Claim {claim_id} has an invalid evidence mapping.")
            for document_key, annotations in evidence_map.items():
                document_id = int(document_key)
                document = corpus.get(document_id)
                if document is None:
                    raise ValueError(f"Claim {claim_id} references missing corpus document {document_id}.")
                if not isinstance(annotations, list):
                    raise ValueError(f"Claim {claim_id} has invalid annotations for document {document_id}.")
                for annotation in annotations:
                    label = self._label(annotation.get("label"), claim_id, document_id)
                    rationale_ids = tuple(int(value) for value in annotation.get("sentences", []))
                    evidence = self._passage(document, rationale_ids)
                    examples.append(SciFactExample(claim_id, claim_text, evidence, label, document_id, rationale_ids))
        return examples

    @staticmethod
    def _passage(document: Mapping[str, Any], sentence_ids: tuple[int, ...]) -> str:
        abstract = document.get("abstract", [])
        if not isinstance(abstract, list) or not all(isinstance(item, str) for item in abstract):
            raise ValueError("SciFact corpus document has an invalid 'abstract'.")
        selected = [abstract[index] for index in sentence_ids if 0 <= index < len(abstract)]
        if not selected:
            selected = abstract
        text = " ".join(selected).strip()
        if not text:
            raise ValueError("SciFact evidence passage is empty.")
        return text

    @staticmethod
    def _label(value: Any, claim_id: int, document_id: int) -> VerificationStatus:
        if not isinstance(value, str) or value.upper() not in _LABEL_MAP:
            raise ValueError(f"Unsupported label for claim {claim_id}, document {document_id}: {value!r}")
        return _LABEL_MAP[value.upper()]

    @staticmethod
    def _require_text(record: Mapping[str, Any], key: str) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"SciFact record is missing non-empty '{key}'.")
        return value.strip()
