"""Context model."""

from dataclasses import asdict, dataclass, field
from typing import Any

from mcp_ui.intent_layer.models.intent import IntentPayload


@dataclass
class ContextResolution:
	"""Resolved runtime context for a user intent."""

	user_id: str
	intent: IntentPayload
	resolved_target: str = ""
	resolved_doc: str = ""
	resolved_entities: dict[str, Any] = field(default_factory=dict)
	recent_docs: list[dict[str, Any]] = field(default_factory=list)
	context_confidence: float = 0.0

	def to_dict(self) -> dict[str, Any]:
		data = asdict(self)
		data["intent"] = self.intent.to_dict()
		return data

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> "ContextResolution":
		payload = payload or {}
		return cls(
			user_id=str(payload.get("user_id") or ""),
			intent=IntentPayload.from_dict(payload.get("intent") or {}),
			resolved_target=str(payload.get("resolved_target") or ""),
			resolved_doc=str(payload.get("resolved_doc") or ""),
			resolved_entities=dict(payload.get("resolved_entities") or {}),
			recent_docs=list(payload.get("recent_docs") or []),
			context_confidence=float(payload.get("context_confidence") or payload.get("confidence") or 0.0),
		)
