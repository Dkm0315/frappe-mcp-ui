from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any

import frappe

from mcp_ui.openclaw.actions import execute_action, get_action_catalog, get_action_metadata
from mcp_ui.openclaw.planner import plan_request_payload, retrieve_site_context
from mcp_ui.openclaw.runtime import get_session_state, write_session_state
from mcp_ui.openclaw.site_context import search_site_context as search_site_context_payload


def _normalize_channel(value: str | None) -> str:
	return (value or "").strip().lower()


def _normalize_username(channel: str, value: str | None) -> str:
	username = (value or "").strip()
	if channel == "telegram":
		username = username.lstrip("@")
	return username.lower()


def _query_tokens(value: str | None) -> list[str]:
	raw = "".join(ch if ch.isalnum() else " " for ch in (value or "").lower()).split()
	stop_words = {"a", "an", "the", "please", "create", "add", "new", "make", "open", "show", "list", "all", "what", "which", "give", "me"}
	return [token for token in raw if token and token not in stop_words]


def _rank_doctype_candidate(name: str, query: str, base_score: int = 0) -> tuple[int, int, int]:
	name_tokens = _query_tokens(name)
	query_tokens = set(_query_tokens(query))
	extra_tokens = [token for token in name_tokens if token not in query_tokens]
	auxiliary_terms = {"activity", "comment", "feedback", "option", "priority", "type", "template", "group", "team", "log"}
	match_bonus = 5 if " ".join(name_tokens) in " ".join(_query_tokens(query)) else 0
	extra_penalty = sum(2 for token in extra_tokens if token in auxiliary_terms) + len(extra_tokens)
	return (base_score + match_bonus - extra_penalty, -len(extra_tokens), -len(name_tokens))


def _iter_identity_mappings(settings) -> list[dict[str, Any]]:
	mappings = []
	for row in settings.get("identity_mappings", []):
		mappings.append(
			{
				"channel": _normalize_channel(row.channel),
				"external_id": (row.external_id or "").strip(),
				"external_username": _normalize_username(row.channel, row.external_username),
				"frappe_user": row.frappe_user,
				"site": row.site or "",
				"enabled": bool(row.enabled),
				"allowed_chat_id": (row.allowed_chat_id or "").strip(),
				"allowed_thread_id": (row.allowed_thread_id or "").strip(),
				"source": "identity_mappings",
			}
		)

	for row in settings.get("telegram_user_mappings", []):
		mappings.append(
			{
				"channel": "telegram",
				"external_id": "",
				"external_username": _normalize_username("telegram", row.telegram_username),
				"frappe_user": row.frappe_user,
				"site": "",
				"enabled": bool(row.enabled),
				"allowed_chat_id": "",
				"allowed_thread_id": "",
				"source": "telegram_user_mappings",
			}
		)

	return mappings


def resolve_identity_record(
	channel: str,
	external_id: str | None = None,
	external_username: str | None = None,
	site_hint: str | None = None,
	chat_id: str | None = None,
	thread_id: str | None = None,
) -> dict[str, Any]:
	settings = frappe.get_single("MCP Settings")
	channel = _normalize_channel(channel)
	site_name = site_hint or frappe.local.site
	normalized_username = _normalize_username(channel, external_username)
	external_id = (external_id or "").strip()
	chat_id = (chat_id or "").strip()
	thread_id = (thread_id or "").strip()

	for row in _iter_identity_mappings(settings):
		if row["channel"] != channel or not row["enabled"]:
			continue
		if row["site"] and row["site"] != site_name:
			continue
		if row["allowed_chat_id"] and row["allowed_chat_id"] != chat_id:
			continue
		if row["allowed_thread_id"] and row["allowed_thread_id"] != thread_id:
			continue

		id_match = bool(external_id and row["external_id"] and row["external_id"] == external_id)
		username_match = bool(
			normalized_username
			and row["external_username"]
			and row["external_username"] == normalized_username
		)

		if not (id_match or username_match):
			continue

		user = frappe.get_doc("User", row["frappe_user"])
		return {
			"success": True,
			"site": site_name,
			"frappe_user": user.name,
			"full_name": user.full_name,
			"enabled": True,
			"roles": [role.role for role in user.roles],
			"matched_on": "external_id" if id_match else "external_username",
			"mapping_source": row["source"],
			"channel": channel,
			"external_id": external_id,
			"external_username": external_username,
		}

	return {
		"success": False,
		"site": site_name,
		"channel": channel,
		"external_id": external_id,
		"external_username": external_username,
		"error": "No enabled identity mapping matched this sender.",
	}


@contextmanager
def impersonate_user(user: str):
	previous_user = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous_user)


def _preflight_document_action(action: str, args: dict[str, Any]) -> dict[str, Any]:
	if action == "create_document":
		doctype = args.get("doctype")
		data = args.get("data") or {}
		doc = frappe.get_doc({"doctype": doctype, **data})
		doc.check_permission("create")
		doc.run_method("before_validate")
		doc.run_method("validate")
		return {"success": True, "doctype": doctype, "validation_only": True}

	if action == "update_document":
		doctype = args.get("doctype")
		name = args.get("name")
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("write")
		doc.update(args.get("data") or {})
		doc.run_method("before_validate")
		doc.run_method("validate")
		return {"success": True, "doctype": doctype, "name": name, "validation_only": True}

	return {
		"success": False,
		"validation_only": True,
		"message": f"Validation preflight is not supported for action '{action}'.",
	}


def _result_status(result: Any, exc: Exception | None = None) -> str:
	if exc:
		if isinstance(exc, frappe.PermissionError):
			return "permission_denied"
		if isinstance(exc, (frappe.ValidationError, frappe.MandatoryError)):
			return "validation_failed"
		return "transient_failure"

	if isinstance(result, dict) and result.get("needs_clarification"):
		return "needs_clarification"
	if isinstance(result, dict) and result.get("status") == "confirmation_required":
		return "confirmation_required"
	if isinstance(result, dict) and result.get("success") is False:
		return "validation_failed"
	return "success"


def _audit_action(user: str, tool_name: str, payload: dict[str, Any], result: Any, status: str) -> None:
	try:
		frappe.get_doc(
			{
				"doctype": "MCP Usage Log",
				"user": user,
				"tool_name": tool_name,
				"parameters": json.dumps(payload, default=str)[:2000],
				"result_summary": json.dumps({"status": status, "result": result}, default=str)[:2000],
				"source": "openclaw_federated",
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


def _session_key(session_context: dict[str, Any]) -> str:
	return (
		session_context.get("session_key")
		or session_context.get("session_id")
		or f"{session_context.get('channel', '')}:{session_context.get('external_id', '')}:{session_context.get('chat_id', '')}"
	)


def get_session_mode_payload(session_context: dict[str, Any]) -> dict[str, Any]:
	resolution = resolve_identity_record(
		channel=session_context.get("channel"),
		external_id=session_context.get("external_id"),
		external_username=session_context.get("external_username"),
		site_hint=session_context.get("site"),
		chat_id=session_context.get("chat_id"),
		thread_id=session_context.get("thread_id"),
	)
	session_key = _session_key(session_context)
	session_state = get_session_state(session_context.get("site"), session_key)
	return {
		"success": bool(resolution.get("success")),
		"session_key": session_key,
		"mode": session_state.get("mode", "normal"),
		"resolution": resolution,
	}


def set_session_mode_payload(session_context: dict[str, Any], mode: str = "normal") -> dict[str, Any]:
	mode = (mode or "normal").strip().lower()
	if mode not in {"normal", "admin"}:
		return {"success": False, "status": "validation_failed", "error": f"Unsupported mode '{mode}'."}

	resolution = resolve_identity_record(
		channel=session_context.get("channel"),
		external_id=session_context.get("external_id"),
		external_username=session_context.get("external_username"),
		site_hint=session_context.get("site"),
		chat_id=session_context.get("chat_id"),
		thread_id=session_context.get("thread_id"),
	)
	if not resolution.get("success"):
		return {
			"success": False,
			"status": "permission_denied",
			"error": resolution.get("error"),
			"resolution": resolution,
		}

	session_key = _session_key(session_context)
	state = write_session_state(
		session_context.get("site"),
		session_key,
		mode=mode,
		frappe_user=resolution["frappe_user"],
		channel=session_context.get("channel"),
	)
	return {
		"success": True,
		"status": "success",
		"session_key": session_key,
		"mode": state.get("mode", mode),
		"resolution": resolution,
	}


def execute_as_mapped_user(
	session_context: dict[str, Any],
	action: str,
	args: dict[str, Any] | None = None,
	validate_only: bool = False,
	confirmed: bool = False,
	confirmation_note: str = "",
) -> dict[str, Any]:
	args = args or {}
	resolution = resolve_identity_record(
		channel=session_context.get("channel"),
		external_id=session_context.get("external_id"),
		external_username=session_context.get("external_username"),
		site_hint=session_context.get("site"),
		chat_id=session_context.get("chat_id"),
		thread_id=session_context.get("thread_id"),
	)

	if not resolution.get("success"):
		return {
			"success": False,
			"status": "permission_denied",
			"error": resolution.get("error"),
			"resolution": resolution,
		}

	action_meta = get_action_metadata(action)
	session_key = _session_key(session_context)
	session_state = get_session_state(session_context.get("site"), session_key)
	if action_meta.get("mode_required") == "admin" and action_meta.get("write") and session_state.get("mode", "normal") != "admin":
		return {
			"success": False,
			"status": "needs_clarification",
			"action": action,
			"frappe_user": resolution["frappe_user"],
			"resolution": resolution,
			"message": "This action requires admin mode. Ask the user to explicitly enter admin mode before continuing.",
		}

	if action_meta.get("write") and not validate_only and not confirmed:
		return {
			"success": False,
			"status": "confirmation_required",
			"action": action,
			"frappe_user": resolution["frappe_user"],
			"resolution": resolution,
			"message": "This action changes data and requires explicit user confirmation before execution.",
			"confirmation_request": {
				"action": action,
				"args": args,
				"note": confirmation_note or "",
			},
		}

	with impersonate_user(resolution["frappe_user"]):
		try:
			result = _preflight_document_action(action, args) if validate_only else execute_action(action, args)
			status = _result_status(result)
			_audit_action(resolution["frappe_user"], action, {"session_context": session_context, "args": args}, result, status)
			return {
				"success": status == "success",
				"status": status,
				"action": action,
				"frappe_user": resolution["frappe_user"],
				"resolution": resolution,
				"result": result,
			}
		except Exception as exc:
			status = _result_status(None, exc=exc)
			_audit_action(
				resolution["frappe_user"],
				action,
				{"session_context": session_context, "args": args},
				{"error": str(exc)},
				status,
			)
			return {
				"success": False,
				"status": status,
				"action": action,
				"frappe_user": resolution["frappe_user"],
				"resolution": resolution,
				"error": str(exc),
			}


def prepare_create_record_payload(
	session_context: dict[str, Any],
	request: str = "",
	doctype: str = "",
	draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
	draft = draft or {}
	resolution = resolve_identity_record(
		channel=session_context.get("channel"),
		external_id=session_context.get("external_id"),
		external_username=session_context.get("external_username"),
		site_hint=session_context.get("site"),
		chat_id=session_context.get("chat_id"),
		thread_id=session_context.get("thread_id"),
	)

	if not resolution.get("success"):
		return {
			"success": False,
			"status": "permission_denied",
			"error": resolution.get("error"),
			"resolution": resolution,
		}

	candidate_doctype = (doctype or "").strip()
	search_result = None

	if not candidate_doctype:
		search_result = retrieve_site_context(
			site=session_context.get("site"),
			query=request,
			limit=12,
		)
		doctype_candidates = [
			{
				"kind": "doctype",
				"name": row.get("name"),
				"score": row.get("score", 0),
				"payload": row.get("payload") or {},
			}
			for row in (search_result.get("groups", {}) or {}).get("doctypes", [])
		]
		doctype_candidates = sorted(
			doctype_candidates,
			key=lambda row: _rank_doctype_candidate(row.get("name", ""), request, row.get("score", 0)),
			reverse=True,
		)
		if not doctype_candidates:
			return {
				"success": False,
				"status": "needs_clarification",
				"resolution": resolution,
				"message": "I could not determine which DocType to create.",
				"suggestions": [],
				"search": search_result,
			}
		top = doctype_candidates[0]
		candidate_doctype = top.get("name", "")
		if len(doctype_candidates) > 1 and _rank_doctype_candidate(
			doctype_candidates[1].get("name", ""),
			request,
			doctype_candidates[1].get("score", 0),
		) >= _rank_doctype_candidate(top.get("name", ""), request, top.get("score", 0)):
			return {
				"success": False,
				"status": "needs_clarification",
				"resolution": resolution,
				"message": "Multiple DocTypes match this create request.",
				"suggestions": [row.get("name") for row in doctype_candidates[:5]],
				"search": search_result,
			}

	from mcp_ui.api.form_builder import get_doctype_form_fields

	with impersonate_user(resolution["frappe_user"]):
		if not frappe.has_permission(candidate_doctype, ptype="create"):
			return {
				"success": False,
				"status": "permission_denied",
				"resolution": resolution,
				"doctype": candidate_doctype,
				"error": f"You don't have create permission for {candidate_doctype}",
			}

		guidance = get_doctype_form_fields(candidate_doctype)
		fields = guidance.get("fields", [])
		required_fields = [field for field in fields if field.get("required")]
		interesting_names = {
			"title", "subject", "description", "summary", "priority", "status",
			"ticket_type", "custom_category", "custom_sub_category", "customer", "contact"
		}
		interesting_fields = [
			field for field in fields
			if field.get("fieldname") in interesting_names
		]
		prefill = {}
		for field in fields:
			default = field.get("default")
			if default not in (None, ""):
				prefill[field["fieldname"]] = default
		prefill.update(draft)

		def _question_for(field: dict[str, Any]) -> str:
			label = field.get("label") or field.get("fieldname")
			if field.get("input_type") == "select" and field.get("options"):
				options = ", ".join(field.get("options", [])[:6])
				return f"What should I set for {label}? Options: {options}"
			return f"What should I put in {label}?"

		missing_required = [field for field in required_fields if not prefill.get(field.get("fieldname"))]
		questions = [_question_for(field) for field in missing_required[:3]]

		if not questions:
			for field in interesting_fields:
				if field.get("fieldname") not in prefill:
					questions.append(_question_for(field))
				if len(questions) >= 3:
					break

		return {
			"success": True,
			"status": "needs_clarification" if questions else "success",
			"resolution": resolution,
			"doctype": candidate_doctype,
			"title_field": guidance.get("title_field"),
			"required_fields": [
				{
					"fieldname": field.get("fieldname"),
					"label": field.get("label"),
					"input_type": field.get("input_type"),
					"options": field.get("options", [])[:10],
				}
				for field in required_fields
			],
			"recommended_fields": [
				{
					"fieldname": field.get("fieldname"),
					"label": field.get("label"),
					"input_type": field.get("input_type"),
					"options": field.get("options", [])[:10],
				}
				for field in interesting_fields[:8]
			],
			"questions": questions,
			"action_plan": {
				"action": "create_document",
				"args": {
					"doctype": candidate_doctype,
					"data": prefill,
				},
				"confirmed": False,
			},
			"search": search_result,
		}


def retrieve_site_context_payload(site: str | None = None, query: str = "", limit: int = 5) -> dict[str, Any]:
	return retrieve_site_context(site=site, query=query, limit=limit)


def plan_request_with_context_payload(
	session_context: dict[str, Any],
	request: str = "",
	draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
	return plan_request_payload(session_context=session_context, request=request, draft=draft or {})


def get_action_catalog_payload(
	query: str = "",
	category: str = "",
	write_only: bool = False,
	destructive_only: bool = False,
	limit: int = 12,
	verbose: bool = False,
) -> dict[str, Any]:
	actions = get_action_catalog()
	category = (category or "").strip().lower()
	query = (query or "").strip().lower()
	limit = max(1, min(limit or 12, 50))

	def _tokenize(value: str) -> list[str]:
		return [token for token in "".join(ch if ch.isalnum() else " " for ch in value).split() if len(token) >= 2]

	query_tokens = _tokenize(query)
	filtered = []
	for action in actions:
		if category and action.get("category", "").lower() != category:
			continue
		if write_only and not action.get("write"):
			continue
		if destructive_only and not action.get("destructive"):
			continue
		searchable_parts = [
			action.get("name", ""),
			action.get("category", ""),
			action.get("description", ""),
			" ".join(action.get("aliases") or []),
		]
		searchable = " ".join(str(part).lower() for part in searchable_parts if part)
		score = 0
		if query:
			if query in searchable:
				score += 10
			for token in query_tokens:
				if token in searchable:
					score += 1
			if score == 0:
				continue
		action = dict(action)
		action["_score"] = score
		filtered.append(action)

	filtered.sort(key=lambda action: (-action.get("_score", 0), action.get("name", "")))
	trimmed = filtered[:limit]
	if verbose:
		return {
			"success": True,
			"count": len(filtered),
			"returned": len(trimmed),
			"actions": trimmed,
		}

	compact_actions = [
		{
			"name": action.get("name"),
			"category": action.get("category"),
			"description": action.get("description"),
			"write": action.get("write"),
			"destructive": action.get("destructive"),
			"mode_required": action.get("mode_required"),
			"execution_path": action.get("execution_path"),
		}
		for action in trimmed
	]
	return {
		"success": True,
		"count": len(filtered),
		"returned": len(compact_actions),
		"query": query,
		"category": category or None,
		"actions": compact_actions,
		"hint": "Use verbose=true only when you need the full filtered list. For ordinary discovery, prefer a narrow query or category.",
	}
