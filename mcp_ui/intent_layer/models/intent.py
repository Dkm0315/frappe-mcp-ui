"""Intent payload model."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class IntentPayload:
	"""Canonical output contract for the intent stage."""

	action: str = "unknown"
	target_candidates: list[str] = field(default_factory=list)
	entities: dict[str, Any] = field(default_factory=dict)
	confidence: float = 0.0
	ambiguity: bool = True
	missing_fields: list[str] = field(default_factory=list)

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> "IntentPayload":
		payload = payload or {}
		return cls(
			action=str(payload.get("action") or "unknown"),
			target_candidates=[str(v) for v in payload.get("target_candidates") or [] if v],
			entities=dict(payload.get("entities") or {}),
			confidence=float(payload.get("confidence") or 0.0),
			ambiguity=bool(payload.get("ambiguity", True)),
			missing_fields=[str(v) for v in payload.get("missing_fields") or [] if v],
		)
