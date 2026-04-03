"""Frappe method API surface for the Intelligent Intent Layer."""

from __future__ import annotations

from typing import Any

import frappe

from mcp_ui.intent_layer.context_engine import ContextEngine
from mcp_ui.intent_layer.customization_engine import CustomizationEngine
from mcp_ui.intent_layer.execution_engine import ExecutionEngine
from mcp_ui.intent_layer.intent_engine import IntentEngine
from mcp_ui.intent_layer.openclaw_adapter import OpenClawAdapter
from mcp_ui.intent_layer.planner import Planner
from mcp_ui.intent_layer.reasoning_engine import ReasoningEngine
from mcp_ui.intent_layer.semantic_engine import SemanticEngine
from mcp_ui.intent_layer.utils.logging import log_stage


@frappe.whitelist(methods=["POST"])
def intent(user_id: str | None = None, message: str | None = None):
	payload = _read_payload({"user_id": user_id, "message": message})
	request_user = _resolve_user(payload.get("user_id"))
	request_id = frappe.generate_hash(length=12)
	intent_payload = IntentEngine().parse(str(payload.get("message") or "")).to_dict()
	log_stage(
		request_id,
		"intent",
		status="Success",
		input_payload={"user_id": request_user, "message": payload.get("message") or ""},
		output_payload=intent_payload,
	)
	return {"intent": intent_payload, "request_id": request_id}


@frappe.whitelist(methods=["POST"])
def context(user_id: str | None = None, intent: dict[str, Any] | str | None = None):
	payload = _read_payload({"user_id": user_id, "intent": intent})
	request_user = _resolve_user(payload.get("user_id"))
	request_id = payload.get("request_id") or frappe.generate_hash(length=12)
	intent_payload = _as_dict(payload.get("intent"))
	context_payload = ContextEngine().resolve(intent_payload, request_user).to_dict()
	log_stage(
		request_id,
		"context",
		status="Success",
		input_payload={"user_id": request_user, "intent": intent_payload},
		output_payload=context_payload,
	)
	return {"context": context_payload, "request_id": request_id}


@frappe.whitelist(methods=["POST"])
def plan(
	user_id: str | None = None,
	intent: dict[str, Any] | str | None = None,
	context: dict[str, Any] | str | None = None,
):
	payload = _read_payload({"user_id": user_id, "intent": intent, "context": context})
	request_user = _resolve_user(payload.get("user_id"))
	request_id = payload.get("request_id") or frappe.generate_hash(length=12)
	try:
		plan_payload, stage_payloads, validation = _build_plan_pipeline(
			request_user=request_user,
			request_id=request_id,
			intent_payload=_as_dict(payload.get("intent")),
			context_payload=_as_dict(payload.get("context")),
		)
		status = "success" if validation.get("allowed") else "failed"
		return {
			"plan": plan_payload,
			"semantic": stage_payloads.get("semantic"),
			"customization": stage_payloads.get("customization"),
			"reasoning": stage_payloads.get("reasoning"),
			"constraints": validation,
			"status": status,
			"request_id": request_id,
		}
	except Exception as exc:
		frappe.log_error(title="Intent Layer Plan Error", message=frappe.get_traceback())
		return _failure_payload(request_id=request_id, message=str(exc), error_type=type(exc).__name__)


@frappe.whitelist(methods=["POST"])
def execute(
	user_id: str | None = None,
	plan: dict[str, Any] | str | None = None,
	request_id: str | None = None,
):
	payload = _read_payload({"user_id": user_id, "plan": plan, "request_id": request_id})
	request_user = _resolve_user(payload.get("user_id"))
	request_id = payload.get("request_id") or frappe.generate_hash(length=12)
	plan_payload = _as_dict(payload.get("plan"))
	try:
		outcome = ExecutionEngine().execute(plan_payload, request_id=request_id, user_id=request_user).to_dict()
		log_stage(
			request_id,
			"execution",
			status="Success" if outcome.get("status") == "completed" else "Failed",
			input_payload=plan_payload,
			output_payload=outcome,
			error_message="; ".join(error.get("message", "") for error in outcome.get("errors") or [] if error),
		)
		return {"execution": outcome, "status": outcome.get("status"), "request_id": request_id}
	except Exception as exc:
		frappe.log_error(title="Intent Layer Execute Error", message=frappe.get_traceback())
		return _failure_payload(
			request_id=request_id,
			plan=plan_payload,
			message=str(exc),
			error_type=type(exc).__name__,
		)


@frappe.whitelist(methods=["POST"])
def run(user_id: str | None = None, message: str | None = None):
	payload = _read_payload({"user_id": user_id, "message": message})
	request_user = _resolve_user(payload.get("user_id"))
	user_message = str(payload.get("message") or "").strip()
	if not user_message:
		frappe.throw("message is required")

	request_id = payload.get("request_id") or frappe.generate_hash(length=12)
	try:
		intent_payload = IntentEngine().parse(user_message).to_dict()
	except Exception as exc:
		frappe.log_error(title="Intent Layer Intent Error", message=frappe.get_traceback())
		return _failure_payload(request_id=request_id, message=str(exc), error_type=type(exc).__name__)
	log_stage(
		request_id,
		"intent",
		status="Success",
		input_payload={"user_id": request_user, "message": user_message},
		output_payload=intent_payload,
	)

	try:
		context_payload = ContextEngine().resolve(intent_payload, request_user).to_dict()
	except Exception as exc:
		frappe.log_error(title="Intent Layer Context Error", message=frappe.get_traceback())
		return _failure_payload(
			request_id=request_id,
			intent=intent_payload,
			message=str(exc),
			error_type=type(exc).__name__,
		)
	log_stage(
		request_id,
		"context",
		status="Success",
		input_payload=intent_payload,
		output_payload=context_payload,
	)

	try:
		plan_payload, stage_payloads, validation = _build_plan_pipeline(
			request_user=request_user,
			request_id=request_id,
			intent_payload=intent_payload,
			context_payload=context_payload,
		)
	except Exception as exc:
		frappe.log_error(title="Intent Layer Run Plan Error", message=frappe.get_traceback())
		return _failure_payload(
			request_id=request_id,
			intent=intent_payload,
			message=str(exc),
			error_type=type(exc).__name__,
		)
	if not validation.get("allowed"):
		execution_payload = {
			"request_id": request_id,
			"plan_id": plan_payload.get("plan_id"),
			"status": "failed",
			"results": [],
			"errors": [
				{
					"error_type": "Validation",
					"severity": "high",
					"recoverable": False,
					"message": "; ".join(validation.get("violations") or []),
				}
			],
		}
		return {
			"intent": intent_payload,
			"plan": plan_payload,
			"execution": execution_payload,
			"status": "failed",
			"request_id": request_id,
		}

	try:
		execution_payload = ExecutionEngine().execute(
			plan_payload,
			request_id=request_id,
			user_id=request_user,
		).to_dict()
	except Exception as exc:
		frappe.log_error(title="Intent Layer Run Execute Error", message=frappe.get_traceback())
		return _failure_payload(
			request_id=request_id,
			intent=intent_payload,
			plan=plan_payload,
			message=str(exc),
			error_type=type(exc).__name__,
		)
	return {
		"intent": intent_payload,
		"plan": plan_payload,
		"execution": execution_payload,
		"status": execution_payload.get("status"),
		"request_id": request_id,
	}


@frappe.whitelist(methods=["GET", "POST"])
def schema(force_refresh: int | str | None = None):
	force = str(force_refresh or "0") in {"1", "true", "True"}
	semantic_registry = SemanticEngine().load_registry(force_refresh=force)
	customization_registry = CustomizationEngine().load_registry(
		force_refresh=force,
		semantic_registry=semantic_registry,
	)
	return {
		"doctypes": list(semantic_registry.doctypes.values()),
		"fields": semantic_registry.fields,
		"relationships": semantic_registry.relationships,
		"workflows": semantic_registry.workflows,
		"permissions": semantic_registry.permissions,
		"aliases": semantic_registry.aliases,
		"samples": semantic_registry.samples,
		"graph": semantic_registry.graph,
		"customizations": customization_registry.to_dict(),
		"refreshed_at": semantic_registry.refreshed_at,
		"checksum": semantic_registry.checksum,
	}


@frappe.whitelist(methods=["GET", "POST"])
def refresh_schema():
	semantic_registry = SemanticEngine().refresh_registry()
	customization_registry = CustomizationEngine().refresh_registry(semantic_registry=semantic_registry)
	return {
		"success": True,
		"site": semantic_registry.site,
		"semantic_checksum": semantic_registry.checksum,
		"customization_checksum": customization_registry.checksum,
		"refreshed_at": semantic_registry.refreshed_at,
		"vector_backend": "FAISS Local" if semantic_registry.faiss_path else "Lexical Fallback",
	}


@frappe.whitelist(methods=["GET", "POST"])
def health():
	settings = frappe.get_single("MCP Settings")
	openclaw_status = OpenClawAdapter().health()
	faiss_ready = bool(settings.get("intent_layer_faiss_path"))
	registry_ready = bool(settings.get("intent_layer_registry_path")) and bool(
		settings.get("intent_layer_customization_path")
	)
	return {
		"status": "ok" if registry_ready else "warming",
		"site": frappe.local.site,
		"registry_ready": registry_ready,
		"faiss_ready": faiss_ready,
		"vector_backend": settings.get("intent_layer_vector_backend") or "Lexical Fallback",
		"last_refresh": settings.get("intent_layer_last_refresh"),
		"schema_checksum": settings.get("intent_layer_schema_checksum"),
		"customization_checksum": settings.get("intent_layer_customization_checksum"),
		"openclaw": openclaw_status,
	}


def _build_plan_pipeline(
	request_user: str,
	request_id: str,
	intent_payload: dict[str, Any],
	context_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
	semantic_payload = SemanticEngine().analyze(context_payload).to_dict()
	log_stage(
		request_id,
		"semantic",
		status="Success",
		input_payload=context_payload,
		output_payload={
			"candidate_count": len(semantic_payload.get("candidates") or []),
			"confidence": semantic_payload.get("confidence"),
			"registry_checksum": semantic_payload.get("registry", {}).get("checksum"),
		},
	)

	customized_payload = CustomizationEngine().apply(semantic_payload)
	semantic_payload = customized_payload.get("semantic") or semantic_payload
	customization_payload = customized_payload.get("customization") or {}
	log_stage(
		request_id,
		"customization",
		status="Success",
		input_payload={
			"candidate_count": len(semantic_payload.get("candidates") or []),
			"selected_target": context_payload.get("resolved_target"),
		},
		output_payload={
			"api_count": len(customization_payload.get("api_map") or {}),
			"rules": len(customization_payload.get("rule_set") or []),
			"checksum": customization_payload.get("checksum"),
		},
	)

	reasoning_payload = ReasoningEngine().reason(semantic_payload, customization_payload)
	log_stage(
		request_id,
		"reasoning",
		status="Success",
		input_payload={"intent": intent_payload, "context": context_payload},
		output_payload=reasoning_payload,
	)

	plan_payload = Planner().build(
		intent_payload=intent_payload,
		context_payload=context_payload,
		semantic_payload=semantic_payload,
		customization_payload=customization_payload,
		reasoning_payload=reasoning_payload,
		user_id=request_user,
	).to_dict()
	validation = ExecutionEngine().constraint_engine.validate_plan(plan_payload.get("steps") or [], request_user)
	if not plan_payload.get("steps"):
		validation = {
			"allowed": False,
			"violations": [_plan_failure_reason(intent_payload, context_payload, reasoning_payload)],
			"suggestions": [_plan_failure_suggestion(reasoning_payload)],
		}
	log_stage(
		request_id,
		"plan",
		status="Success" if validation.get("allowed") else "Failed",
		input_payload={"reasoning": reasoning_payload},
		output_payload={"plan": plan_payload, "constraints": validation},
		error_message="; ".join(validation.get("violations") or []),
		error_type="Validation" if not validation.get("allowed") else "",
	)
	return (
		plan_payload,
		{
			"semantic": semantic_payload,
			"customization": customization_payload,
			"reasoning": reasoning_payload,
		},
		validation,
	)


def _resolve_user(user_id: str | None) -> str:
	session_user = frappe.session.user
	request_user = user_id or session_user
	if request_user != session_user and "System Manager" not in frappe.get_roles(session_user):
		raise frappe.PermissionError("Only System Manager can execute the intent layer on behalf of another user.")
	if not frappe.db.exists("User", request_user):
		frappe.throw(f"Unknown user_id: {request_user}")
	return request_user


def _read_payload(explicit: dict[str, Any]) -> dict[str, Any]:
	payload = {
		key: value
		for key, value in (explicit or {}).items()
		if value is not None
	}
	try:
		if getattr(frappe.local, "request", None) and frappe.request:
			body = frappe.request.get_json(silent=True) or {}
			if isinstance(body, dict):
				for key, value in body.items():
					if value is not None:
						payload.setdefault(key, value)
	except Exception:
		pass
	return payload


def _as_dict(payload: dict[str, Any] | str | None) -> dict[str, Any]:
	if isinstance(payload, dict):
		return payload
	if isinstance(payload, str) and payload.strip():
		try:
			parsed = frappe.parse_json(payload)
			return parsed if isinstance(parsed, dict) else {}
		except Exception:
			return {}
	return {}


def _failure_payload(
	request_id: str,
	message: str,
	error_type: str,
	intent: dict[str, Any] | None = None,
	plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
	return {
		"intent": intent or {},
		"plan": plan or {"steps": [], "status": "failed"},
		"execution": {
			"request_id": request_id,
			"plan_id": (plan or {}).get("plan_id"),
			"status": "failed",
			"results": [],
			"errors": [
				{
					"error_type": error_type or "System",
					"severity": "high",
					"recoverable": False,
					"message": message,
				}
			],
		},
		"status": "failed",
		"request_id": request_id,
	}


def _plan_failure_reason(
	intent_payload: dict[str, Any],
	context_payload: dict[str, Any],
	reasoning_payload: dict[str, Any],
) -> str:
	if reasoning_payload.get("action") == "unknown" or intent_payload.get("action") == "unknown":
		return "The request action is ambiguous or unsupported."
	if not reasoning_payload.get("selected_target") and context_payload.get("resolved_target"):
		return f"Unknown DocType or alias: {context_payload.get('resolved_target')}"
	if reasoning_payload.get("ambiguity"):
		candidates = [
			row.get("doctype")
			for row in reasoning_payload.get("valid_candidates") or []
			if row.get("doctype")
		]
		if candidates:
			return f"Ambiguous request; candidate targets: {', '.join(candidates[:5])}"
	return "No executable plan could be generated for this request."


def _plan_failure_suggestion(reasoning_payload: dict[str, Any]) -> str:
	candidates = [
		row.get("doctype")
		for row in reasoning_payload.get("valid_candidates") or []
		if row.get("doctype")
	]
	if candidates:
		return f"Clarify the action and one target DocType, for example: {candidates[0]}."
	return "Clarify the target business object, document name, or action."
