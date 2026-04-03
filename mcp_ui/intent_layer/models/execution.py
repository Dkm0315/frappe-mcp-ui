"""Execution output models."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StepOutcome:
	step_id: str
	action: str
	tool: str
	status: str
	input: dict[str, Any] = field(default_factory=dict)
	output: dict[str, Any] = field(default_factory=dict)
	error: dict[str, Any] | None = None
	retry_count: int = 0

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)


@dataclass
class ExecutionOutcome:
	request_id: str
	plan_id: str
	status: str = "pending"
	results: list[StepOutcome] = field(default_factory=list)
	errors: list[dict[str, Any]] = field(default_factory=list)

	def to_dict(self) -> dict[str, Any]:
		return {
			"request_id": self.request_id,
			"plan_id": self.plan_id,
			"status": self.status,
			"results": [result.to_dict() for result in self.results],
			"errors": self.errors,
		}
