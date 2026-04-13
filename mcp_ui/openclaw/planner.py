from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

import frappe

from mcp_ui.openclaw.actions import get_action_catalog
from mcp_ui.openclaw.runtime import get_session_state
from mcp_ui.openclaw.site_context import get_site_manifest


INTENT_KEYWORDS = {
	"create": {"create", "add", "new", "make", "raise", "open"},
	"update": {"update", "edit", "change", "modify", "set", "mark"},
	"delete": {"delete", "remove", "cancel", "archive"},
	"report": {"report", "analytics", "analysis", "metric", "summary", "dashboard", "sla", "response", "trend"},
	"inventory": {"what", "which", "list", "show", "present", "available", "all"},
	"workflow": {"workflow", "approve", "approval", "transition", "status", "pending"},
	"ui": {"screen", "page", "desk", "form", "ui", "click", "button", "navigate", "open page"},
	"admin": {"script", "custom field", "property setter", "workflow design", "doctype", "customize", "funnel", "server script", "client script"},
	"code": {"hook", "override", "permission", "doc event", "server script", "client script", "code", "logic"},
}

SECTION_MAP = {
	"apps": "apps",
	"modules": "modules",
	"doctypes": "doctypes",
	"report": "reports",
	"reports": "reports",
	"workflow": "workflows",
	"workflows": "workflows",
	"page": "pages",
	"workspace": "workspaces",
	"custom field": "custom_fields",
	"property setter": "property_setters",
	"client script": "client_scripts",
	"server script": "server_scripts",
	"hook": "hooks",
	"funnel": "nextai",
}

QUERY_SYNONYMS = {
	"employee": ["hr", "staff"],
	"response": ["first response", "sla", "resolution"],
	"report": ["analytics", "summary", "dashboard"],
	"workflow": ["approval", "state", "transition"],
}


def _tokenize(value: str) -> list[str]:
	return [token for token in "".join(ch if ch.isalnum() else " " for ch in (value or "").lower()).split() if token]


def _expanded_tokens(query: str) -> list[str]:
	tokens = _tokenize(query)
	expanded = set(tokens)
	for token in list(tokens):
		for extra in QUERY_SYNONYMS.get(token, []):
			expanded.update(_tokenize(extra))
	for key, section in SECTION_MAP.items():
		if key in (query or "").lower():
			expanded.update(_tokenize(key))
			expanded.update(_tokenize(section))
	return sorted(expanded)


def _text_blob(value: Any) -> str:
	if value is None:
		return ""
	if isinstance(value, dict):
		return " ".join(_text_blob(item) for item in value.values())
	if isinstance(value, (list, tuple, set)):
		return " ".join(_text_blob(item) for item in value)
	return str(value).lower()


def _score(tokens: list[str], *parts: Any) -> int:
	haystack = _text_blob(parts)
	score = 0
	for token in tokens:
		if token in haystack:
			score += 2 if haystack.startswith(token) else 1
	for token in tokens:
		if f" {token} " in f" {haystack} ":
			score += 1
	return score


def _detect_intents(request: str) -> list[str]:
	lowered = (request or "").lower()
	intents = []
	create_phrases = ("create a ", "create an ", "create new", "add a ", "add an ", "raise a ", "open a ")
	if any(phrase in lowered for phrase in create_phrases) and "report" not in lowered:
		intents.append("create")
	for intent, keywords in INTENT_KEYWORDS.items():
		if intent == "create":
			continue
		if any(keyword in lowered for keyword in keywords):
			intents.append(intent)
	if not intents:
		intents = ["inventory"] if "?" in lowered else ["report"]
	return intents


def _action_score(query_tokens: list[str], action: dict[str, Any], intents: list[str]) -> int:
	score = _score(query_tokens, action.get("name"), action.get("description"), action.get("aliases"))
	if action.get("surface") == "primitive":
		score -= 2
	if "report" in intents and action.get("name") == "run_report":
		score += 6
	if "inventory" in intents and action.get("name") == "get_list":
		score += 5
	if any(intent in intents for intent in ("create", "update")) and action.get("write"):
		score += 4
	if "create" in intents and action.get("name") == "create_document":
		score += 8
	if "create" in intents and action.get("name") == "get_form_guidance":
		score += 5
	if "workflow" in intents and action.get("category") == "workflow":
		score += 4
	if "admin" in intents and action.get("mode_required") == "admin":
		score += 5
	if "ui" in intents and action.get("execution_path") == "ui":
		score += 4
	if action.get("mode_required") == "admin" and "admin" not in intents and "code" not in intents:
		score -= 4
	return score


def retrieve_site_context(site: str | None = None, query: str = "", limit: int = 5) -> dict[str, Any]:
	manifest = get_site_manifest(site=site, refresh=False, detail_level="full")
	query_tokens = _expanded_tokens(query)
	limit = max(1, min(limit or 5, 12))
	grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

	def add(group: str, name: str, payload: dict[str, Any], *parts: Any) -> None:
		score = _score(query_tokens, *parts)
		if score <= 0:
			return
		grouped[group].append({"name": name, "score": score, "payload": payload})

	for app in manifest.get("apps", []):
		add("apps", app.get("name"), {"title": app.get("title"), "modules": app.get("modules", [])[:8]}, app)

	module_map: dict[str, set[str]] = defaultdict(set)
	for doctype in manifest.get("doctypes", []):
		module_map[doctype.get("module") or "Other"].add(doctype.get("name") or "")
		add(
			"doctypes",
			doctype.get("name"),
			{
				"module": doctype.get("module"),
				"custom": doctype.get("custom"),
				"description": doctype.get("description"),
			},
			doctype,
		)
	for module, names in module_map.items():
		add("modules", module, {"sample_doctypes": sorted(names)[:8], "doctype_count": len(names)}, module, sorted(names))

	for report in manifest.get("reports", []):
		add("reports", report.get("name"), report, report)

	for workflow in manifest.get("workflows", []):
		add("workflows", workflow.get("name"), workflow, workflow)

	for page in manifest.get("pages", []):
		add("pages", page.get("name"), page, page)
	for workspace in manifest.get("workspaces", []):
		add("workspaces", workspace.get("name"), workspace, workspace)
	for field in manifest.get("custom_fields", []):
		add("custom_fields", field.get("name"), field, field)
	for setter in manifest.get("property_setters", []):
		add("property_setters", setter.get("name"), setter, setter)
	for script in manifest.get("client_scripts", []):
		add("client_scripts", script.get("name"), script, script)
	for script in manifest.get("server_scripts", []):
		add("server_scripts", script.get("name"), script, script)

	hooks = manifest.get("hooks", {}) or {}
	for hook_group, hook_payload in hooks.items():
		add("hooks", hook_group, {"group": hook_group, "entries": hook_payload}, hook_group, hook_payload)

	nextai = manifest.get("nextai", {}) or {}
	for funnel in nextai.get("published", []) or []:
		add("nextai", funnel.get("name"), funnel, funnel)
	for workflow in nextai.get("workflows", []) or []:
		add("nextai", workflow.get("name"), workflow, workflow)

	action_results = []
	for action in get_action_catalog():
		score = _action_score(query_tokens, action, _detect_intents(query))
		if score > 0:
			action_results.append(
				{
					"name": action.get("name"),
					"score": score,
					"payload": {
						"category": action.get("category"),
						"write": action.get("write"),
						"mode_required": action.get("mode_required"),
						"execution_path": action.get("execution_path"),
						"surface": action.get("surface"),
						"description": action.get("description"),
					},
				}
			)
	grouped["actions"] = action_results

	for key in list(grouped):
		grouped[key] = sorted(grouped[key], key=lambda row: (-row.get("score", 0), row.get("name") or ""))[:limit]

	return {
		"success": True,
		"site": manifest.get("site"),
		"query": query,
		"manifest_hash": manifest.get("manifest_hash"),
		"groups": grouped,
	}


def _session_key(session_context: dict[str, Any]) -> str:
	return (
		session_context.get("session_key")
		or session_context.get("session_id")
		or f"{session_context.get('channel', '')}:{session_context.get('external_id', '')}:{session_context.get('chat_id', '')}"
	)


def _execution_path(intents: list[str], retrieval: dict[str, Any]) -> str:
	if "ui" in intents:
		return "ui"
	if any(intent in intents for intent in ("create", "update", "delete", "report", "inventory", "workflow")):
		return "server"
	if retrieval.get("groups", {}).get("pages") or retrieval.get("groups", {}).get("workspaces"):
		return "ui"
	return "server"


def _doctype_choice_score(name: str, query: str) -> tuple[int, int]:
	query_tokens = set(_expanded_tokens(query))
	name_tokens = _tokenize(name)
	extra_tokens = [token for token in name_tokens if token not in query_tokens]
	extra_penalty = sum(2 for token in extra_tokens if token in {"activity", "comment", "feedback", "option", "template", "priority", "type", "summary"})
	exact_bonus = 4 if " ".join(name_tokens) in " ".join(_expanded_tokens(query)) else 0
	return (exact_bonus - extra_penalty - len(extra_tokens), -len(name_tokens))


def _choose_top_doctype(request: str, retrieval: dict[str, Any], top_report_row: dict[str, Any] | None = None) -> str | None:
	doctypes = retrieval.get("groups", {}).get("doctypes") or []
	if top_report_row:
		ref_doctype = (top_report_row.get("payload") or {}).get("ref_doctype")
		if ref_doctype:
			return ref_doctype
	if not doctypes:
		return None
	sorted_doctypes = sorted(
		doctypes,
		key=lambda row: (_doctype_choice_score(row.get("name", ""), request), row.get("score", 0)),
		reverse=True,
	)
	return sorted_doctypes[0].get("name")


def _related_reports(retrieval: dict[str, Any], top_doctype: str | None, top_report: str | None) -> list[dict[str, Any]]:
	reports = retrieval.get("groups", {}).get("reports") or []
	if not reports:
		return []
	if top_doctype:
		matched = [row for row in reports if (row.get("payload") or {}).get("ref_doctype") == top_doctype]
		if matched:
			return matched[:5]
	if top_report:
		matched = [row for row in reports if row.get("name") == top_report]
		if matched:
			return matched[:1]
	return reports[:5]


def _permission_probe(resolution: dict[str, Any], doctype: str | None = None, report: str | None = None) -> dict[str, Any]:
	result: dict[str, Any] = {}
	from mcp_ui.openclaw.federation import impersonate_user

	with impersonate_user(resolution["frappe_user"]):
		if doctype:
			result["doctype"] = doctype
			result["can_read"] = bool(frappe.has_permission(doctype, ptype="read"))
			result["can_create"] = bool(frappe.has_permission(doctype, ptype="create"))
			result["can_write"] = bool(frappe.has_permission(doctype, ptype="write"))
		if report:
			try:
				result["report"] = report
				result["can_run_report"] = bool(frappe.has_permission("Report", ptype="read", doc=report))
			except Exception:
				result["can_run_report"] = False
	return result


def plan_request_payload(
	session_context: dict[str, Any],
	request: str = "",
	draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
	from mcp_ui.openclaw.federation import prepare_create_record_payload, resolve_identity_record

	draft = draft or {}
	request = (request or "").strip()
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

	intents = _detect_intents(request)
	retrieval = retrieve_site_context(site=session_context.get("site"), query=request, limit=5)
	session_state = get_session_state(session_context.get("site"), _session_key(session_context))
	mode = session_state.get("mode", "normal")
	top_report_row = ((retrieval.get("groups", {}).get("reports") or [{}])[0])
	top_report = top_report_row.get("name")
	top_doctype = _choose_top_doctype(request, retrieval, top_report_row=top_report_row)
	top_actions = retrieval.get("groups", {}).get("actions") or []
	related_reports = _related_reports(retrieval, top_doctype, top_report)
	permission_summary = _permission_probe(resolution, doctype=top_doctype, report=top_report)
	requires_admin_mode = any(intent in intents for intent in ("admin", "code")) or any(
		action.get("payload", {}).get("mode_required") == "admin" for action in top_actions[:3]
	)

	if requires_admin_mode and mode != "admin":
		return {
			"success": True,
			"status": "needs_clarification",
			"request": request,
			"resolution": resolution,
			"session_mode": mode,
			"mode_required": "admin",
			"message": "This request touches customization or system-design capability. Ask the user to enter admin mode before proposing or applying the change.",
			"retrieval": retrieval,
			"intents": intents,
		}

	create_plan = None
	if "create" in intents:
		create_plan = prepare_create_record_payload(
			session_context=session_context,
			request=request,
			draft=draft,
		)
		if create_plan.get("doctype"):
			top_doctype = create_plan.get("doctype")

	candidate_actions = []
	for action in top_actions[:5]:
		payload = action.get("payload", {})
		candidate_actions.append(
			{
				"name": action.get("name"),
				"category": payload.get("category"),
				"write": payload.get("write"),
				"mode_required": payload.get("mode_required"),
				"execution_path": payload.get("execution_path"),
				"surface": payload.get("surface"),
				"reason": "matched request terms and detected intent",
			}
		)

	plan_steps = []
	if "inventory" in intents and top_doctype:
		plan_steps.append(f"List visible {top_doctype} records for the mapped user.")
	if "report" in intents and top_report:
		plan_steps.append(f"Run or inspect report '{top_report}' if the mapped user has access.")
	if "workflow" in intents:
		plan_steps.append("Inspect current workflow state and valid next transitions before acting.")
	if create_plan and create_plan.get("questions"):
		plan_steps.append("Ask the missing field questions before attempting create.")
	if any(action.get("write") for action in candidate_actions):
		plan_steps.append("Confirm the write with the user before execution.")

	return {
		"success": True,
		"status": create_plan.get("status") if create_plan else "success",
		"request": request,
		"resolution": resolution,
		"session_mode": mode,
		"intents": intents,
		"execution_path": _execution_path(intents, retrieval),
		"retrieval": retrieval,
		"candidate_actions": candidate_actions,
		"top_doctype": top_doctype,
		"top_report": top_report,
		"related_reports": [
			{
				"name": row.get("name"),
				"module": (row.get("payload") or {}).get("module"),
				"ref_doctype": (row.get("payload") or {}).get("ref_doctype"),
				"report_type": (row.get("payload") or {}).get("report_type"),
			}
			for row in related_reports
		],
		"answer_constraints": {
			"focus_doctype": top_doctype,
			"focus_report": top_report,
			"use_only_related_reports": True,
			"mention_permissions_explicitly": True,
			"do_not_list_unrelated_modules": True,
		},
		"permission_summary": permission_summary,
		"missing_inputs": create_plan.get("questions", []) if create_plan else [],
		"create_plan": create_plan,
		"confirmation_required": any(action.get("write") for action in candidate_actions),
		"plan_steps": plan_steps,
		"answer_style": "answer_plus_method",
	}
