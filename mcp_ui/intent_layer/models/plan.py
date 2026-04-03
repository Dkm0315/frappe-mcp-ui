"""Plan models."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PlanStep:
	step_id: str
	action: str
	target: str
	input: dict[str, Any] = field(default_factory=dict)
	tool: str = ""
	dependencies: list[str] = field(default_factory=list)
	status: str = "pending"
	idempotent: bool = True
	sensitive: bool = False

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> "PlanStep":
		payload = payload or {}
		return cls(
			step_id=str(payload.get("step_id") or payload.get("step") or ""),
			action=str(payload.get("action") or ""),
			target=str(payload.get("target") or ""),
			input=dict(payload.get("input") or {}),
			tool=str(payload.get("tool") or ""),
			dependencies=[str(v) for v in payload.get("dependencies") or [] if v],
			status=str(payload.get("status") or "pending"),
			idempotent=bool(payload.get("idempotent", True)),
			sensitive=bool(payload.get("sensitive", False)),
		)


@dataclass
class PlanEnvelope:
	plan_id: str
	intent: dict[str, Any]
	context: dict[str, Any]
	semantic: dict[str, Any]
	customization: dict[str, Any]
	reasoning: dict[str, Any]
	steps: list[PlanStep] = field(default_factory=list)
	status: str = "pending"

	def to_dict(self) -> dict[str, Any]:
		return {
			"plan_id": self.plan_id,
			"intent": self.intent,
			"context": self.context,
			"semantic": self.semantic,
			"customization": self.customization,
			"reasoning": self.reasoning,
			"steps": [step.to_dict() for step in self.steps],
			"status": self.status,
		}

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> "PlanEnvelope":
		payload = payload or {}
		return cls(
			plan_id=str(payload.get("plan_id") or ""),
			intent=dict(payload.get("intent") or {}),
			context=dict(payload.get("context") or {}),
			semantic=dict(payload.get("semantic") or {}),
			customization=dict(payload.get("customization") or {}),
			reasoning=dict(payload.get("reasoning") or {}),
			steps=[PlanStep.from_dict(step) for step in payload.get("steps") or []],
			status=str(payload.get("status") or "pending"),
		)
