"""Deterministic error classification and recovery decisions."""

from __future__ import annotations

from typing import Any

import frappe

from mcp_ui.intent_layer.models.error import ClassifiedError, RecoveryDecision


class ErrorHandler:
	"""Classify failures and choose safe recovery strategies."""

	def classify(self, exc: Exception | dict[str, Any], step_id: str = "") -> ClassifiedError:
		message = ""
		exc_type = ""
		if isinstance(exc, dict):
			error_payload = exc.get("error") or {}
			message = str(error_payload.get("message") or exc.get("message") or "")
			exc_type = str(error_payload.get("type") or exc.get("type") or "")
		else:
			message = str(exc)
			exc_type = type(exc).__name__

		lowered = f"{exc_type} {message}".lower()
		if "permission" in lowered or isinstance(exc, frappe.PermissionError):
			return ClassifiedError("Permission", "high", False, message, step_id)
		if "openclaw" in lowered or "gateway" in lowered or "transport" in lowered or "timeout" in lowered:
			return ClassifiedError("Transport", "high", True, message, step_id)
		if "mandatory" in lowered or "required" in lowered or "missing" in lowered:
			return ClassifiedError("Missing Data", "medium", True, message, step_id)
		if "linkvalidationerror" in lowered or "not found" in lowered or "does not exist" in lowered:
			return ClassifiedError("Dependency", "medium", True, message, step_id)
		if "validation" in lowered or "workflow" in lowered or "transition" in lowered:
			return ClassifiedError("Validation", "medium", True, message, step_id)
		return ClassifiedError("System", "high", True, message, step_id)

	def choose_recovery(
		self,
		classified: ClassifiedError,
		failed_input: dict[str, Any] | None = None,
		retry_count: int = 0,
		max_retries: int = 2,
	) -> RecoveryDecision:
		failed_input = failed_input or {}
		if classified.error_type == "Permission":
			return RecoveryDecision(strategy="escalate", retry=False, replan=False)
		if classified.error_type == "Missing Data":
			return RecoveryDecision(
				strategy="request_input",
				corrected_input=failed_input,
				retry=False,
				replan=False,
			)
		if classified.error_type == "Dependency":
			return RecoveryDecision(
				strategy="replan",
				corrected_input=failed_input,
				retry=False,
				replan=True,
			)
		if classified.error_type == "Validation":
			return RecoveryDecision(
				strategy="correct_and_retry" if retry_count < max_retries else "replan",
				corrected_input=failed_input,
				retry=retry_count < max_retries,
				replan=retry_count >= max_retries,
			)
		if classified.error_type == "Transport":
			return RecoveryDecision(
				strategy="retry_runtime" if retry_count < max_retries else "fallback_or_escalate",
				corrected_input=failed_input,
				retry=retry_count < max_retries,
				replan=False,
			)
		return RecoveryDecision(
			strategy="retry" if retry_count < max_retries else "escalate",
			corrected_input=failed_input,
			retry=retry_count < max_retries,
			replan=False,
		)
