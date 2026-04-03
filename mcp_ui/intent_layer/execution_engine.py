"""Planner-driven execution loop with deterministic recovery boundaries."""

from __future__ import annotations

from typing import Any

from mcp_ui.intent_layer.constraint_engine import ConstraintEngine
from mcp_ui.intent_layer.context_engine import ContextEngine
from mcp_ui.intent_layer.error_handler import ErrorHandler
from mcp_ui.intent_layer.models.execution import ExecutionOutcome, StepOutcome
from mcp_ui.intent_layer.models.plan import PlanEnvelope
from mcp_ui.intent_layer.openclaw_adapter import OpenClawAdapter
from mcp_ui.intent_layer.utils.logging import log_stage


class ExecutionEngine:
	"""Execute deterministic plan steps and recover safely where possible."""

	MAX_RETRIES = 2

	def __init__(self):
		self.constraint_engine = ConstraintEngine()
		self.error_handler = ErrorHandler()
		self.openclaw_adapter = OpenClawAdapter()
		self.context_engine = ContextEngine()

	def execute(self, plan_payload: dict[str, Any], request_id: str, user_id: str) -> ExecutionOutcome:
		plan = PlanEnvelope.from_dict(plan_payload)
		outcome = ExecutionOutcome(request_id=request_id, plan_id=plan.plan_id, status="running")
		completed_steps: dict[str, dict[str, Any]] = {}

		for step in plan.steps:
			step_payload = step.to_dict()
			retry_count = 0

			while True:
				pre_validation = self.constraint_engine.validate_step(step_payload, user_id)
				if not pre_validation.get("allowed"):
					classified = self.error_handler.classify(
						{"error": {"type": "ValidationError", "message": "; ".join(pre_validation.get("violations") or [])}},
						step_id=step.step_id,
					)
					outcome.errors.append(classified.to_dict())
					outcome.results.append(
						StepOutcome(
							step_id=step.step_id,
							action=step.action,
							tool=step.tool,
							status="failed",
							input=step_payload.get("input") or {},
							output={"validation": pre_validation},
							error=classified.to_dict(),
							retry_count=retry_count,
						)
					)
					log_stage(
						request_id,
						f"execute:{step.step_id}:{step.tool}",
						status="Failed",
						input_payload=step_payload,
						output_payload={"validation": pre_validation},
						error_message=classified.message,
						retry_count=retry_count,
						error_type=classified.error_type,
					)
					outcome.status = "failed"
					return outcome

				call_input = self._resolve_step_input(step_payload.get("input") or {}, completed_steps)
				result = self.openclaw_adapter.execute(step.tool, call_input)
				if result.get("status") == "success":
					step_output = result.get("data") or {}
					post_validation_error = self._validate_step_success(step_payload, call_input, step_output)
					if post_validation_error:
						result = {
							"status": "error",
							"data": step_output,
							"error": {
								"type": "ValidationError",
								"message": post_validation_error,
							},
						}
					else:
						outcome.results.append(
							StepOutcome(
								step_id=step.step_id,
								action=step.action,
								tool=step.tool,
								status="success",
								input=call_input,
								output={**step_output, "_runtime": result.get("runtime")},
								error=None,
								retry_count=retry_count,
							)
						)
						completed_steps[step.step_id] = step_output
						self._remember_output(user_id, step_output)
						log_stage(
							request_id,
							f"execute:{step.step_id}:{step.tool}",
							status="Success",
							input_payload=call_input,
							output_payload={**step_output, "_runtime": result.get("runtime")},
							retry_count=retry_count,
						)
						break

				classified = self.error_handler.classify(result, step_id=step.step_id)
				recovery = self.error_handler.choose_recovery(
					classified,
					failed_input=call_input,
					retry_count=retry_count,
					max_retries=self.MAX_RETRIES,
				)
				log_stage(
					request_id,
					f"execute:{step.step_id}:{step.tool}",
					status="Failed",
					input_payload=call_input,
					output_payload=result,
					error_message=classified.message,
					retry_count=retry_count,
					error_type=classified.error_type,
				)
				if recovery.retry and not step.sensitive:
					retry_count += 1
					step_payload["input"] = recovery.corrected_input or call_input
					continue
				outcome.errors.append(
					{
						**classified.to_dict(),
						"recovery": recovery.to_dict(),
					}
				)
				outcome.results.append(
					StepOutcome(
						step_id=step.step_id,
						action=step.action,
						tool=step.tool,
						status="failed",
						input=call_input,
						output={**(result.get("data") or {}), "_runtime": result.get("runtime")},
						error={**classified.to_dict(), "recovery": recovery.to_dict()},
						retry_count=retry_count,
					)
				)
				outcome.status = "failed"
				return outcome

		outcome.status = "completed"
		return outcome

	def _resolve_step_input(
		self,
		step_input: dict[str, Any],
		completed_steps: dict[str, dict[str, Any]],
	) -> dict[str, Any]:
		updated = dict(step_input or {})
		if not completed_steps:
			return updated

		last_output = list(completed_steps.values())[-1]
		if updated.get("doctype") == "Payment Entry":
			data = dict(updated.get("data") or {})
			doc = last_output.get("doc") or {}
			if doc and not data.get("party"):
				data["party"] = doc.get("customer") or doc.get("party") or data.get("party")
			if doc and not data.get("paid_amount"):
				data["paid_amount"] = doc.get("outstanding_amount") or doc.get("grand_total") or 0
			if doc and not data.get("received_amount"):
				data["received_amount"] = data.get("paid_amount") or 0
			updated["data"] = data

		if not updated.get("name") and last_output.get("name") and updated.get("doctype") == last_output.get("doctype"):
			updated["name"] = last_output.get("name")
		return updated

	def _remember_output(self, user_id: str, output: dict[str, Any]) -> None:
		doctype = output.get("doctype") or (output.get("doc") or {}).get("doctype")
		name = output.get("name") or (output.get("doc") or {}).get("name")
		if doctype and name:
			self.context_engine.remember_document(user_id, doctype, name)

	def _validate_step_success(
		self,
		step_payload: dict[str, Any],
		call_input: dict[str, Any],
		step_output: dict[str, Any],
	) -> str:
		tool = step_payload.get("tool")
		action = str(step_payload.get("action") or "").lower()
		if tool != "call_custom_api" or action != "custom_api":
			return ""

		method = str(call_input.get("method") or step_output.get("method") or "")
		params = dict(step_output.get("params") or call_input.get("params") or {})
		result = step_output.get("result")
		is_mutating = not bool(step_payload.get("idempotent"))
		if not is_mutating:
			return ""

		if result in (None, "", [], {}) and not step_output.get("name") and not step_output.get("doc"):
			return f"Custom API {method} returned an empty result for a mutating action."
		if not params and result in (None, "", [], {}):
			return f"Custom API {method} executed with no accepted parameters and no observable output."
		return ""
