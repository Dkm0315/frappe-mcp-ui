"""Error classification models."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ClassifiedError:
	error_type: str
	severity: str
	recoverable: bool
	message: str = ""
	step_id: str = ""

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)


@dataclass
class RecoveryDecision:
	strategy: str
	corrected_input: dict[str, Any] = field(default_factory=dict)
	retry: bool = False
	replan: bool = False

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)
