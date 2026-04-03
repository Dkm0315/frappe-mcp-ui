"""Semantic registry and candidate models."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SemanticCandidate:
	doctype: str
	score: float = 0.0
	fields: dict[str, Any] = field(default_factory=dict)
	workflow: dict[str, Any] = field(default_factory=dict)
	permissions: list[dict[str, Any]] = field(default_factory=list)
	relationships: list[dict[str, Any]] = field(default_factory=list)

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)


@dataclass
class SemanticRegistry:
	site: str
	doctypes: dict[str, dict[str, Any]] = field(default_factory=dict)
	fields: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
	relationships: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
	workflows: dict[str, dict[str, Any]] = field(default_factory=dict)
	permissions: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
	aliases: dict[str, str] = field(default_factory=dict)
	samples: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
	graph: dict[str, list[str]] = field(default_factory=dict)
	faiss_path: str = ""
	faiss_map_path: str = ""
	checksum: str = ""
	refreshed_at: str = ""

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> "SemanticRegistry":
		payload = payload or {}
		return cls(
			site=str(payload.get("site") or ""),
			doctypes=dict(payload.get("doctypes") or {}),
			fields=dict(payload.get("fields") or {}),
			relationships=dict(payload.get("relationships") or {}),
			workflows=dict(payload.get("workflows") or {}),
			permissions=dict(payload.get("permissions") or {}),
			aliases=dict(payload.get("aliases") or {}),
			samples=dict(payload.get("samples") or {}),
			graph=dict(payload.get("graph") or {}),
			faiss_path=str(payload.get("faiss_path") or ""),
			faiss_map_path=str(payload.get("faiss_map_path") or ""),
			checksum=str(payload.get("checksum") or ""),
			refreshed_at=str(payload.get("refreshed_at") or ""),
		)


@dataclass
class SemanticResult:
	intent: dict[str, Any]
	context: dict[str, Any]
	candidates: list[SemanticCandidate] = field(default_factory=list)
	registry: SemanticRegistry = field(default_factory=lambda: SemanticRegistry(site=""))
	confidence: float = 0.0

	def to_dict(self) -> dict[str, Any]:
		return {
			"intent": self.intent,
			"context": self.context,
			"candidates": [candidate.to_dict() for candidate in self.candidates],
			"registry": self.registry.to_dict(),
			"confidence": self.confidence,
		}
