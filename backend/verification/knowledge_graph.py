"""A lightweight, evidence-derived knowledge graph."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import networkx as nx

from retrieval.retrieve import RetrievedDocument

_ENTITY_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*)*\b")


@dataclass(frozen=True)
class GraphRelation:
    """An edge backed by the evidence document that expressed it."""

    subject: str
    predicate: str
    object: str
    source: str


class EvidenceKnowledgeGraph:
    """Create source-to-entity ``mentions`` edges without inventing facts."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def add_evidence(self, documents: Iterable[RetrievedDocument]) -> None:
        for document in documents:
            source_id = f"source:{document.source}:{document.title}"
            self.graph.add_node(source_id, kind="source", label=document.title)
            for entity in self.extract_entities(document.content):
                self.graph.add_node(entity, kind="entity", label=entity)
                self.graph.add_edge(source_id, entity, predicate="mentions", source=document.source)

    def extract_entities(self, text: str) -> list[str]:
        """Return capitalised spans explicitly present in supplied evidence text."""
        return sorted(set(match.group(0) for match in _ENTITY_PATTERN.finditer(text)))

    def find_mentions(self, entity: str) -> list[GraphRelation]:
        """Return evidence-backed mention edges for an exact entity label."""
        if entity not in self.graph:
            return []
        relations: list[GraphRelation] = []
        for source_id, _, data in self.graph.in_edges(entity, data=True):
            relations.append(
                GraphRelation(
                    subject=self.graph.nodes[source_id]["label"],
                    predicate=str(data["predicate"]),
                    object=entity,
                    source=str(data["source"]),
                )
            )
        return relations
