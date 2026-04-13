from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import frappe

from mcp_ui.openclaw.runtime import compute_hash, ensure_runtime_dirs, read_json, write_json
from mcp_ui.openclaw.skills import generate_site_skills
from mcp_ui.utils.app_checker import is_nextai_installed


def _app_git_ref(app_name: str, bench_path: str) -> str | None:
	app_path = Path(bench_path) / "apps" / app_name
	if not (app_path / ".git").exists():
		return None

	try:
		result = subprocess.run(
			["git", "-C", str(app_path), "rev-parse", "HEAD"],
			check=False,
			capture_output=True,
			text=True,
			timeout=5,
		)
		if result.returncode == 0:
			return result.stdout.strip()
	except Exception:
		pass

	return None


def _get_app_records(bench_path: str) -> list[dict[str, Any]]:
	apps = []
	for app_name in frappe.get_installed_apps():
		try:
			modules = frappe.get_module_list(app_name) if app_name != "frappe" else []
		except Exception:
			modules = []

		apps.append(
			{
				"name": app_name,
				"title": (frappe.get_hooks("app_title", app_name=app_name) or [app_name])[0],
				"modules": modules,
				"git_ref": _app_git_ref(app_name, bench_path),
			}
		)
	return apps


def _get_doctypes() -> list[dict[str, Any]]:
	return frappe.get_all(
		"DocType",
		filters={"istable": 0},
		fields=[
			"name",
			"module",
			"custom",
			"is_submittable",
			"issingle",
			"is_tree",
			"description",
			"modified",
		],
		order_by="module asc, name asc",
	)


def _get_workflows() -> list[dict[str, Any]]:
	workflows = frappe.get_all(
		"Workflow",
		fields=["name", "document_type", "is_active", "modified", "workflow_state_field"],
		order_by="modified desc",
	)

	for workflow in workflows:
		doc = frappe.get_doc("Workflow", workflow["name"])
		workflow["states"] = [
			{"state": row.state, "doc_status": row.doc_status, "allow_edit": row.allow_edit}
			for row in doc.states
		]
		workflow["transitions"] = [
			{"state": row.state, "action": row.action, "next_state": row.next_state, "allowed": row.allowed}
			for row in doc.transitions
		]

	return workflows


def _get_custom_fields() -> list[dict[str, Any]]:
	return frappe.get_all(
		"Custom Field",
		fields=["name", "dt", "fieldname", "label", "fieldtype", "options", "insert_after", "modified"],
		order_by="modified desc",
	)


def _get_property_setters() -> list[dict[str, Any]]:
	return frappe.get_all(
		"Property Setter",
		fields=["name", "doc_type", "field_name", "property", "value", "property_type", "modified"],
		order_by="modified desc",
	)


def _get_reports() -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Report"):
		return []
	return frappe.get_all(
		"Report",
		fields=["name", "ref_doctype", "report_type", "module", "modified"],
		order_by="modified desc",
	)


def _get_workspaces() -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Workspace"):
		return []
	return frappe.get_all(
		"Workspace",
		fields=["name", "module", "public", "for_user", "modified"],
		order_by="modified desc",
	)


def _get_pages() -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Page"):
		return []
	return frappe.get_all(
		"Page",
		fields=["name", "module", "standard", "modified"],
		order_by="modified desc",
	)


def _get_client_scripts() -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Client Script"):
		return []
	return frappe.get_all(
		"Client Script",
		fields=["name", "dt", "enabled", "view", "module", "modified"],
		order_by="modified desc",
	)


def _get_server_scripts() -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Server Script"):
		return []
	return frappe.get_all(
		"Server Script",
		fields=[
			"name",
			"script_type",
			"reference_doctype",
			"doctype_event",
			"api_method",
			"disabled",
			"module",
			"modified",
		],
		order_by="modified desc",
	)


def _get_nextai_funnels() -> dict[str, Any]:
	if not is_nextai_installed():
		return {"installed": False, "published": [], "workflows": []}

	meta = frappe.get_meta("Funnel Published")
	fields = ["name", "funnel", "modified"]
	if meta.has_field("funnel_description"):
		fields.append("funnel_description")

	published = frappe.get_all(
		"Funnel Published",
		filters={"published": 1},
		fields=fields,
		order_by="modified desc",
	)

	workflows = []
	if frappe.db.exists("DocType", "Funnel Workflow"):
		workflows = frappe.get_all(
			"Funnel Workflow",
			fields=["name", "funnel", "status", "modified"],
			order_by="modified desc",
			limit=50,
		)

	return {"installed": True, "published": published, "workflows": workflows}


def _get_hooks_snapshot() -> dict[str, Any]:
	return {
		"doc_events": frappe.get_hooks("doc_events") or {},
		"override_doctype_class": frappe.get_hooks("override_doctype_class") or {},
		"permission_query_conditions": frappe.get_hooks("permission_query_conditions") or {},
		"has_permission": frappe.get_hooks("has_permission") or {},
	}


def _system_counts() -> dict[str, int]:
	return {
		"apps": len(frappe.get_installed_apps()),
		"doctypes": frappe.db.count("DocType", {"istable": 0}),
		"custom_fields": frappe.db.count("Custom Field"),
		"property_setters": frappe.db.count("Property Setter"),
		"workflows": frappe.db.count("Workflow"),
		"reports": frappe.db.count("Report") if frappe.db.exists("DocType", "Report") else 0,
		"client_scripts": frappe.db.count("Client Script") if frappe.db.exists("DocType", "Client Script") else 0,
		"server_scripts": frappe.db.count("Server Script") if frappe.db.exists("DocType", "Server Script") else 0,
	}


def build_site_manifest(site: str | None = None) -> dict[str, Any]:
	paths = ensure_runtime_dirs(site)
	bench_path = paths["bench_path"]

	manifest = {
		"site": paths["site"],
		"generated_at": datetime.utcnow().isoformat(),
		"apps": _get_app_records(bench_path),
		"doctypes": _get_doctypes(),
		"custom_fields": _get_custom_fields(),
		"property_setters": _get_property_setters(),
		"workflows": _get_workflows(),
		"reports": _get_reports(),
		"workspaces": _get_workspaces(),
		"pages": _get_pages(),
		"client_scripts": _get_client_scripts(),
		"server_scripts": _get_server_scripts(),
		"hooks": _get_hooks_snapshot(),
		"nextai": _get_nextai_funnels(),
		"system": {"counts": _system_counts()},
	}

	manifest["manifest_hash"] = compute_hash(manifest)
	manifest["system"]["source_hash"] = compute_hash(
		{
			"apps": [(app["name"], app.get("git_ref")) for app in manifest["apps"]],
			"counts": manifest["system"]["counts"],
		}
	)
	return manifest


def _summarize_manifest(manifest: dict[str, Any], sections: list[str] | None = None, limit_per_section: int = 10) -> dict[str, Any]:
	sections = sections or ["apps", "modules", "doctypes", "workflows", "reports", "customizations", "nextai"]
	limit_per_section = max(1, min(limit_per_section or 10, 25))

	module_map: dict[str, dict[str, Any]] = {}
	for doctype in manifest.get("doctypes", []):
		module = doctype.get("module") or "Other"
		entry = module_map.setdefault(module, {"module": module, "doctype_count": 0, "sample_doctypes": []})
		entry["doctype_count"] += 1
		if len(entry["sample_doctypes"]) < 5:
			entry["sample_doctypes"].append(doctype.get("name"))

	sorted_modules = sorted(module_map.values(), key=lambda item: (-item["doctype_count"], item["module"]))
	sorted_doctypes = sorted(manifest.get("doctypes", []), key=lambda item: ((item.get("module") or ""), item.get("name") or ""))

	summary = {
		"success": True,
		"site": manifest.get("site"),
		"manifest_hash": manifest.get("manifest_hash"),
		"generated_at": manifest.get("generated_at"),
		"counts": manifest.get("system", {}).get("counts", {}),
		"sections": {},
	}

	if "apps" in sections:
		summary["sections"]["apps"] = [
			{
				"name": app.get("name"),
				"title": app.get("title"),
				"module_count": len(app.get("modules") or []),
				"modules": (app.get("modules") or [])[:5],
				"git_ref": app.get("git_ref"),
			}
			for app in manifest.get("apps", [])[:limit_per_section]
		]

	if "modules" in sections:
		summary["sections"]["modules"] = sorted_modules[:limit_per_section]

	if "doctypes" in sections:
		summary["sections"]["doctypes"] = [
			{
				"name": row.get("name"),
				"module": row.get("module"),
				"custom": row.get("custom"),
				"is_submittable": row.get("is_submittable"),
			}
			for row in sorted_doctypes[:limit_per_section]
		]

	if "workflows" in sections:
		summary["sections"]["workflows"] = [
			{
				"name": workflow.get("name"),
				"document_type": workflow.get("document_type"),
				"is_active": workflow.get("is_active"),
				"transition_count": len(workflow.get("transitions") or []),
			}
			for workflow in manifest.get("workflows", [])[:limit_per_section]
		]

	if "reports" in sections:
		summary["sections"]["reports"] = [
			{
				"name": report.get("name"),
				"module": report.get("module"),
				"ref_doctype": report.get("ref_doctype"),
				"report_type": report.get("report_type"),
			}
			for report in manifest.get("reports", [])[:limit_per_section]
		]

	if "customizations" in sections:
		summary["sections"]["customizations"] = {
			"custom_fields": [
				{
					"dt": field.get("dt"),
					"fieldname": field.get("fieldname"),
					"label": field.get("label"),
					"fieldtype": field.get("fieldtype"),
				}
				for field in manifest.get("custom_fields", [])[:limit_per_section]
			],
			"property_setters": [
				{
					"doc_type": setter.get("doc_type"),
					"field_name": setter.get("field_name"),
					"property": setter.get("property"),
					"value": setter.get("value"),
				}
				for setter in manifest.get("property_setters", [])[:limit_per_section]
			],
		}

	if "nextai" in sections:
		nextai = manifest.get("nextai", {}) or {}
		summary["sections"]["nextai"] = {
			"installed": bool(nextai.get("installed")),
			"published_count": len(nextai.get("published") or []),
			"workflow_count": len(nextai.get("workflows") or []),
			"published": (nextai.get("published") or [])[:limit_per_section],
			"workflows": (nextai.get("workflows") or [])[:limit_per_section],
		}

	return summary


def search_site_context(
	site: str | None = None,
	query: str = "",
	sections: list[str] | None = None,
	limit: int = 12,
) -> dict[str, Any]:
	manifest = get_site_manifest(site, refresh=False, detail_level="full")
	query = (query or "").strip().lower()
	limit = max(1, min(limit or 12, 30))
	sections = set(sections or ["apps", "modules", "doctypes", "workflows", "reports", "pages", "workspaces", "custom_fields", "property_setters", "client_scripts", "server_scripts"])

	if not query:
		return {
			"success": True,
			"site": manifest.get("site"),
			"query": query,
			"results": [],
			"message": "Provide a search query to match apps, modules, doctypes, workflows, reports, scripts, or customizations.",
		}

	def _tokens(value: Any) -> str:
		if value is None:
			return ""
		if isinstance(value, (list, tuple)):
			return " ".join(_tokens(item) for item in value)
		if isinstance(value, dict):
			return " ".join(_tokens(item) for item in value.values())
		return str(value).lower()

	def _score(haystack: str) -> int:
		score = 0
		for token in query.split():
			if token in haystack:
				score += 2 if haystack.startswith(token) else 1
		if query in haystack:
			score += 3
		return score

	results = []

	def _add(kind: str, name: str, payload: dict[str, Any], keys: list[Any]):
		haystack = _tokens(keys)
		score = _score(haystack)
		if score <= 0:
			return
		results.append(
			{
				"kind": kind,
				"name": name,
				"score": score,
				"payload": payload,
			}
		)

	if "apps" in sections:
		for app in manifest.get("apps", []):
			_add(
				"app",
				app.get("name"),
				{"title": app.get("title"), "modules": app.get("modules", [])[:8], "git_ref": app.get("git_ref")},
				[app.get("name"), app.get("title"), app.get("modules", [])],
			)

	if "modules" in sections:
		for doctype in manifest.get("doctypes", []):
			module = doctype.get("module") or "Other"
			_add("module", module, {"sample_doctype": doctype.get("name")}, [module, doctype.get("name")])

	if "doctypes" in sections:
		for doctype in manifest.get("doctypes", []):
			_add(
				"doctype",
				doctype.get("name"),
				{
					"module": doctype.get("module"),
					"custom": doctype.get("custom"),
					"description": doctype.get("description"),
				},
				[doctype.get("name"), doctype.get("module"), doctype.get("description")],
			)

	if "workflows" in sections:
		for workflow in manifest.get("workflows", []):
			_add(
				"workflow",
				workflow.get("name"),
				{
					"document_type": workflow.get("document_type"),
					"is_active": workflow.get("is_active"),
					"state_count": len(workflow.get("states") or []),
					"transition_count": len(workflow.get("transitions") or []),
				},
				[
					workflow.get("name"),
					workflow.get("document_type"),
					[state.get("state") for state in workflow.get("states") or []],
					[transition.get("action") for transition in workflow.get("transitions") or []],
				],
			)

	if "reports" in sections:
		for report in manifest.get("reports", []):
			_add(
				"report",
				report.get("name"),
				{
					"module": report.get("module"),
					"ref_doctype": report.get("ref_doctype"),
					"report_type": report.get("report_type"),
				},
				[report.get("name"), report.get("module"), report.get("ref_doctype"), report.get("report_type")],
			)

	if "pages" in sections:
		for page in manifest.get("pages", []):
			_add("page", page.get("name"), {"module": page.get("module"), "standard": page.get("standard")}, [page.get("name"), page.get("module")])

	if "workspaces" in sections:
		for workspace in manifest.get("workspaces", []):
			_add("workspace", workspace.get("name"), {"module": workspace.get("module"), "public": workspace.get("public")}, [workspace.get("name"), workspace.get("module")])

	if "custom_fields" in sections:
		for field in manifest.get("custom_fields", []):
			_add(
				"custom_field",
				field.get("name"),
				{
					"dt": field.get("dt"),
					"fieldname": field.get("fieldname"),
					"label": field.get("label"),
					"fieldtype": field.get("fieldtype"),
				},
				[field.get("name"), field.get("dt"), field.get("fieldname"), field.get("label"), field.get("fieldtype"), field.get("options")],
			)

	if "property_setters" in sections:
		for setter in manifest.get("property_setters", []):
			_add(
				"property_setter",
				setter.get("name"),
				{
					"doc_type": setter.get("doc_type"),
					"field_name": setter.get("field_name"),
					"property": setter.get("property"),
					"value": setter.get("value"),
				},
				[setter.get("name"), setter.get("doc_type"), setter.get("field_name"), setter.get("property"), setter.get("value")],
			)

	if "client_scripts" in sections:
		for script in manifest.get("client_scripts", []):
			_add("client_script", script.get("name"), {"dt": script.get("dt"), "module": script.get("module"), "view": script.get("view")}, [script.get("name"), script.get("dt"), script.get("module"), script.get("view")])

	if "server_scripts" in sections:
		for script in manifest.get("server_scripts", []):
			_add(
				"server_script",
				script.get("name"),
				{
					"script_type": script.get("script_type"),
					"reference_doctype": script.get("reference_doctype"),
					"doctype_event": script.get("doctype_event"),
					"api_method": script.get("api_method"),
				},
				[script.get("name"), script.get("script_type"), script.get("reference_doctype"), script.get("doctype_event"), script.get("api_method")],
			)

	results.sort(key=lambda item: (-item["score"], item["kind"], item["name"] or ""))
	trimmed = results[:limit]
	return {
		"success": True,
		"site": manifest.get("site"),
		"query": query,
		"result_count": len(trimmed),
		"results": trimmed,
	}


def _build_diff(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
	if not previous:
		return {
			"summary": ["Initial manifest generated."],
			"app_changes": [],
			"counts_delta": current.get("system", {}).get("counts", {}),
		}

	summary = []
	app_changes = []
	prev_apps = {app["name"]: app for app in previous.get("apps", [])}
	curr_apps = {app["name"]: app for app in current.get("apps", [])}

	for app_name in sorted(set(prev_apps) | set(curr_apps)):
		prev = prev_apps.get(app_name)
		curr = curr_apps.get(app_name)
		if not prev:
			summary.append(f"App added: {app_name}")
			app_changes.append({"app": app_name, "change": "added"})
			continue
		if not curr:
			summary.append(f"App removed: {app_name}")
			app_changes.append({"app": app_name, "change": "removed"})
			continue
		if prev.get("git_ref") != curr.get("git_ref"):
			summary.append(f"App updated: {app_name}")
			app_changes.append(
				{
					"app": app_name,
					"change": "updated",
					"from": prev.get("git_ref"),
					"to": curr.get("git_ref"),
				}
			)

	counts_delta = {}
	for key, value in current.get("system", {}).get("counts", {}).items():
		previous_value = previous.get("system", {}).get("counts", {}).get(key, 0)
		if value != previous_value:
			counts_delta[key] = {"from": previous_value, "to": value}
			summary.append(f"{key.replace('_', ' ').title()} changed from {previous_value} to {value}")

	return {
		"summary": summary or ["No structural changes detected."],
		"app_changes": app_changes,
		"counts_delta": counts_delta,
	}


def refresh_site_context(site: str | None = None, reason: str = "manual") -> dict[str, Any]:
	paths = ensure_runtime_dirs(site)
	previous = read_json(paths["manifest_file"], None)
	current = build_site_manifest(site)
	diff = _build_diff(previous, current)
	diff["reason"] = reason
	diff["generated_at"] = current["generated_at"]

	if previous:
		write_json(paths["previous_manifest_file"], previous)

	write_json(paths["manifest_file"], current)
	write_json(paths["manifest_diff_file"], diff)
	skills = generate_site_skills(current)

	try:
		settings = frappe.get_single("MCP Settings")
		settings.db_set("openclaw_runtime_root", paths["root"], update_modified=False)
		settings.db_set("openclaw_manifest_hash", current["manifest_hash"], update_modified=False)
		settings.db_set("openclaw_last_manifest_refresh", current["generated_at"], update_modified=False)
	except Exception:
		pass

	return {
		"success": True,
		"site": current["site"],
		"manifest_hash": current["manifest_hash"],
		"generated_at": current["generated_at"],
		"diff": diff,
		"skills": skills,
	}


def get_site_manifest(
	site: str | None = None,
	refresh: bool = False,
	detail_level: str = "summary",
	sections: list[str] | None = None,
	limit_per_section: int = 10,
) -> dict[str, Any]:
	paths = ensure_runtime_dirs(site)
	if refresh or not Path(paths["manifest_file"]).exists():
		refresh_site_context(site, reason="api_refresh" if refresh else "bootstrap")
	manifest = read_json(paths["manifest_file"], {})
	if (detail_level or "summary").lower() == "full":
		return manifest
	return _summarize_manifest(manifest, sections=sections, limit_per_section=limit_per_section)


def get_change_summary(site: str | None = None, since_hash_or_timestamp: str | None = None) -> dict[str, Any]:
	paths = ensure_runtime_dirs(site)
	current = get_site_manifest(site)
	diff = read_json(paths["manifest_diff_file"], {}) or {}

	if since_hash_or_timestamp and current.get("manifest_hash") == since_hash_or_timestamp:
		return {"success": True, "site": current.get("site"), "changes": [], "message": "No changes since that manifest hash."}

	return {
		"success": True,
		"site": current.get("site"),
		"manifest_hash": current.get("manifest_hash"),
		"summary": diff.get("summary", []),
		"app_changes": diff.get("app_changes", []),
		"counts_delta": diff.get("counts_delta", {}),
	}


def mark_manifest_stale(doc=None, method: str | None = None):
	try:
		refresh_site_context(reason=f"hook:{getattr(doc, 'doctype', 'unknown')}:{method or 'update'}")
	except Exception as exc:
		frappe.log_error(str(exc), "OpenClaw Manifest Refresh Failed")


def scheduled_refresh_context():
	current = get_site_manifest(refresh=False)
	if not current:
		refresh_site_context(reason="scheduled_bootstrap")
		return

	rebuilt = build_site_manifest()
	if rebuilt.get("system", {}).get("source_hash") != current.get("system", {}).get("source_hash"):
		refresh_site_context(reason="scheduled_source_hash_change")
