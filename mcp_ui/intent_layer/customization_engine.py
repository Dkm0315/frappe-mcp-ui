"""Customization scanner for code, scripts, APIs, and UI routes."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import frappe

from mcp_ui.intent_layer.models.customization import CustomizationRegistry
from mcp_ui.intent_layer.models.semantic import SemanticRegistry
from mcp_ui.intent_layer.utils.cache import cache_get, cache_set
from mcp_ui.intent_layer.utils.parsers import (
	extract_rule_snippets,
	infer_doctype_from_controller_path,
	parse_hooks_file,
	parse_python_controller,
	safe_read_text,
)


class CustomizationEngine:
	"""Extract custom DocTypes, fields, controllers, hooks, scripts, APIs, and routes."""

	CACHE_KEY = "customization_registry"
	REGISTRY_FILE = "intent_layer_customization_registry.json"

	def refresh_registry(self, semantic_registry: SemanticRegistry | None = None) -> CustomizationRegistry:
		semantic_registry = semantic_registry or SemanticRegistry.from_dict({})
		custom_doctypes = self._scan_custom_doctypes()
		custom_fields = self._scan_custom_fields()
		controllers = self._scan_controllers()
		hooks = self._scan_hooks()
		server_scripts = self._scan_server_scripts()
		client_scripts = self._scan_client_scripts()
		api_map = self._scan_whitelisted_apis(controllers)
		ui_routes = self._scan_ui_routes()
		behavior_graph, rule_set = self._build_behavior_graph(
			custom_doctypes=custom_doctypes,
			custom_fields=custom_fields,
			controllers=controllers,
			hooks=hooks,
			server_scripts=server_scripts,
			client_scripts=client_scripts,
			api_map=api_map,
			semantic_registry=semantic_registry,
		)

		registry = CustomizationRegistry(
			site=frappe.local.site,
			custom_doctypes=custom_doctypes,
			custom_fields=custom_fields,
			controllers=controllers,
			hooks=hooks,
			server_scripts=server_scripts,
			client_scripts=client_scripts,
			api_map=api_map,
			ui_routes=ui_routes,
			behavior_graph=behavior_graph,
			rule_set=rule_set,
			refreshed_at=str(frappe.utils.now_datetime()),
		)
		registry.checksum = self._checksum_registry(registry.to_dict())
		self._persist_registry(registry)
		cache_set(self.CACHE_KEY, registry.to_dict(), expires_in_sec=3600)
		return registry

	def load_registry(self, force_refresh: bool = False, semantic_registry: SemanticRegistry | None = None) -> CustomizationRegistry:
		if not force_refresh:
			cached = cache_get(self.CACHE_KEY)
			if cached:
				return CustomizationRegistry.from_dict(cached)

		settings = frappe.get_single("MCP Settings")
		registry_path = settings.get("intent_layer_customization_path")
		if not force_refresh and registry_path and os.path.exists(registry_path):
			try:
				payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
				registry = CustomizationRegistry.from_dict(payload)
				cache_set(self.CACHE_KEY, registry.to_dict(), expires_in_sec=3600)
				return registry
			except Exception:
				pass
		return self.refresh_registry(semantic_registry=semantic_registry)

	def apply(self, semantic_payload: dict[str, Any]) -> dict[str, Any]:
		semantic_registry = SemanticRegistry.from_dict(semantic_payload.get("registry") or {})
		registry = self.load_registry(semantic_registry=semantic_registry)
		semantic_payload = self._boost_semantic_candidates(semantic_payload, registry)
		return {
			"semantic": semantic_payload,
			"customization": registry.to_dict(),
		}

	def _scan_custom_doctypes(self) -> dict[str, dict[str, Any]]:
		rows = frappe.get_all(
			"DocType",
			filters={"custom": 1},
			fields=["name", "module", "description", "is_submittable"],
			order_by="name asc",
		)
		result = {}
		for row in rows:
			meta = frappe.get_meta(row.name)
			result[row.name] = {
				"doctype": row.name,
				"module": row.module,
				"is_custom": True,
				"description": row.description or "",
				"is_submittable": bool(row.is_submittable),
				"fields": [
					{
						"fieldname": field.fieldname,
						"label": field.label or field.fieldname,
						"fieldtype": field.fieldtype,
						"required": bool(field.reqd),
						"options": field.options or "",
						"depends_on": field.depends_on or "",
					}
					for field in meta.fields
					if field.fieldtype not in {"Section Break", "Column Break", "Tab Break"}
				],
			}
		return result

	def _scan_custom_fields(self) -> dict[str, list[dict[str, Any]]]:
		rows = frappe.get_all(
			"Custom Field",
			fields=["name", "dt", "fieldname", "label", "fieldtype", "options", "reqd", "depends_on"],
			order_by="dt asc, idx asc",
		)
		result: dict[str, list[dict[str, Any]]] = {}
		for row in rows:
			result.setdefault(row.dt, []).append(
				{
					"name": row.name,
					"dt": row.dt,
					"fieldname": row.fieldname,
					"label": row.label or row.fieldname,
					"fieldtype": row.fieldtype,
					"options": row.options or "",
					"required": bool(row.reqd),
					"depends_on": row.depends_on or "",
				}
			)
		return result

	def _scan_controllers(self) -> dict[str, dict[str, Any]]:
		controllers: dict[str, dict[str, Any]] = {}
		for app in frappe.get_installed_apps():
			app_path = Path(frappe.get_app_path(app)).resolve()
			for path in app_path.rglob("doctype/*/*.py"):
				if path.name == "__init__.py":
					continue
				if ".git" in path.parts or "__pycache__" in path.parts:
					continue
				doctype = infer_doctype_from_controller_path(path)
				if not doctype:
					continue
				payload = parse_python_controller(path)
				source = safe_read_text(path)
				payload["rules"] = [*payload.get("rules", []), *extract_rule_snippets(source)]
				payload["app"] = app
				controllers[doctype] = payload
		return controllers

	def _scan_hooks(self) -> dict[str, Any]:
		hook_map: dict[str, Any] = {}
		for app in frappe.get_installed_apps():
			app_path = Path(frappe.get_app_path(app)).resolve()
			path = app_path / "hooks.py"
			if not path.exists():
				continue
			hook_map[app] = parse_hooks_file(path)
		return hook_map

	def _scan_server_scripts(self) -> list[dict[str, Any]]:
		if not frappe.db.exists("DocType", "Server Script"):
			return []
		fieldnames = _available_fields(
			"Server Script",
			["name", "script_type", "reference_doctype", "doctype_event", "event", "api_method", "disabled", "script"],
		)
		scripts = frappe.get_all(
			"Server Script",
			fields=fieldnames,
			order_by="modified desc",
		)
		return [
			{
				"name": row.name,
				"script_type": row.get("script_type"),
				"reference_doctype": row.get("reference_doctype"),
				"event": row.get("doctype_event") or row.get("event"),
				"api_method": row.get("api_method"),
				"disabled": bool(row.get("disabled")),
				"rules": extract_rule_snippets(row.get("script") or ""),
			}
			for row in scripts
		]

	def _scan_client_scripts(self) -> list[dict[str, Any]]:
		if not frappe.db.exists("DocType", "Client Script"):
			return []
		fieldnames = _available_fields(
			"Client Script",
			["name", "dt", "enabled", "view", "script"],
		)
		scripts = frappe.get_all(
			"Client Script",
			fields=fieldnames,
			order_by="modified desc",
		)
		return [
			{
				"name": row.name,
				"dt": row.get("dt"),
				"enabled": bool(row.get("enabled", True)),
				"view": row.get("view"),
				"rules": extract_rule_snippets(row.get("script") or ""),
			}
			for row in scripts
		]

	def _scan_whitelisted_apis(self, controllers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
		api_map: dict[str, dict[str, Any]] = {}
		for app in frappe.get_installed_apps():
			app_root = Path(frappe.get_app_path(app)).resolve()
			for path in app_root.rglob("*.py"):
				if "__pycache__" in path.parts or ".git" in path.parts:
					continue
				if path.name == "__init__.py":
					continue
				parsed = parse_python_controller(path)
				signatures = parsed.get("whitelisted_signatures") or {}
				for fn_name in parsed.get("whitelisted_methods") or []:
					module_path = path.relative_to(app_root.parent).with_suffix("")
					method = ".".join(module_path.parts + (fn_name,))
					signature = signatures.get(fn_name) or {}
					api_map[method] = {
						"method": method,
						"app": app,
						"module": ".".join(module_path.parts),
						"function": fn_name,
						"doctype": infer_doctype_from_controller_path(path),
						"action": _infer_action_from_method(fn_name),
						"parameters": signature.get("parameters") or [],
						"required_params": signature.get("required_params") or [],
						"optional_params": signature.get("optional_params") or [],
						"accepts_kwargs": bool(signature.get("accepts_kwargs")),
					}

		if frappe.db.exists("DocType", "Server Script"):
			for script in frappe.get_all(
				"Server Script",
				filters={"script_type": "API", "disabled": 0},
				fields=["name", "api_method"],
			):
				if script.api_method:
					api_map[script.api_method] = {
						"method": script.api_method,
						"app": "server_script",
						"module": "Server Script",
						"function": script.name,
						"doctype": "",
						"action": _infer_action_from_method(script.api_method),
						"parameters": [],
						"required_params": [],
						"optional_params": [],
						"accepts_kwargs": True,
					}

		for doctype, controller in controllers.items():
			signatures = controller.get("whitelisted_signatures") or {}
			for fn_name in controller.get("whitelisted_methods") or []:
				controller_path = str(controller.get("path") or "")
				if "/" in controller_path or controller_path.endswith(".py"):
					continue
				method = f"{controller_path}.{fn_name}"
				signature = signatures.get(fn_name) or {}
				api_map.setdefault(
					method,
					{
						"method": method,
						"app": controller.get("app"),
						"module": controller.get("path"),
						"function": fn_name,
						"doctype": doctype,
						"action": _infer_action_from_method(fn_name),
						"parameters": signature.get("parameters") or [],
						"required_params": signature.get("required_params") or [],
						"optional_params": signature.get("optional_params") or [],
						"accepts_kwargs": bool(signature.get("accepts_kwargs")),
					},
				)
		return api_map

	def _scan_ui_routes(self) -> list[dict[str, Any]]:
		routes: list[dict[str, Any]] = []
		for app in frappe.get_installed_apps():
			app_root = Path(frappe.get_app_path(app)).resolve()
			www_path = app_root / "www"
			if www_path.exists():
				for path in www_path.rglob("*.py"):
					routes.append(
						{
							"app": app,
							"route": f"/{path.relative_to(www_path).with_suffix('').as_posix()}",
							"source": str(path),
							"type": "website_page",
						}
					)

		spa_router = Path(frappe.get_app_path("mcp_ui")).resolve().parent / "mcp" / "src" / "router" / "index.tsx"
		if spa_router.exists():
			source = safe_read_text(spa_router)
			for match in re.finditer(r'path\s*:\s*["\']([^"\']+)["\']', source):
				routes.append(
					{
						"app": "mcp_ui",
						"route": match.group(1),
						"source": str(spa_router),
						"type": "spa_route",
					}
				)
		return routes

	def _build_behavior_graph(
		self,
		custom_doctypes: dict[str, dict[str, Any]],
		custom_fields: dict[str, list[dict[str, Any]]],
		controllers: dict[str, dict[str, Any]],
		hooks: dict[str, Any],
		server_scripts: list[dict[str, Any]],
		client_scripts: list[dict[str, Any]],
		api_map: dict[str, dict[str, Any]],
		semantic_registry: SemanticRegistry,
	) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
		_ = custom_doctypes
		behavior_graph: dict[str, list[dict[str, Any]]] = {}
		rule_set: list[dict[str, Any]] = []

		for doctype, rows in custom_fields.items():
			for row in rows:
				node = {
					"type": "custom_field",
					"fieldname": row["fieldname"],
					"required": row["required"],
					"depends_on": row["depends_on"],
				}
				behavior_graph.setdefault(doctype, []).append(node)
				if row["depends_on"] or row["required"]:
					rule_set.append(
						{
							"doctype": doctype,
							"rule": "custom_field_constraint",
							"condition": row["depends_on"] or f"{row['fieldname']} required",
							"action": "validate_before_execution",
						}
					)

		for doctype, controller in controllers.items():
			for rule in controller.get("rules") or []:
				behavior_graph.setdefault(doctype, []).append(
					{
						"type": "controller_rule",
						"event": rule.get("event", "runtime"),
						"condition": rule.get("condition", ""),
						"action": rule.get("action", ""),
					}
				)
				rule_set.append(
					{
						"doctype": doctype,
						"rule": "controller_validation",
						"condition": rule.get("condition") or rule.get("event") or "controller logic",
						"action": rule.get("action") or "validate",
					}
				)

		for app, hook_payload in hooks.items():
			for doctype, events in (hook_payload.get("doc_events") or {}).items():
				if isinstance(events, dict):
					for event, handler in events.items():
						behavior_graph.setdefault(doctype, []).append(
							{
								"type": "hook",
								"event": event,
								"handler": handler,
								"app": app,
							}
						)
						rule_set.append(
							{
								"doctype": doctype,
								"rule": "doc_event_hook",
								"condition": event,
								"action": str(handler),
							}
						)

		for script in server_scripts:
			doctype = script.get("reference_doctype") or ""
			if not doctype:
				continue
			behavior_graph.setdefault(doctype, []).append(
				{
					"type": "server_script",
					"event": script.get("event") or script.get("script_type"),
					"name": script.get("name"),
					"api_method": script.get("api_method"),
				}
			)
			for rule in script.get("rules") or []:
				rule_set.append(
					{
						"doctype": doctype,
						"rule": "server_script_rule",
						"condition": rule.get("condition") or "script",
						"action": rule.get("action") or script.get("name"),
					}
				)

		for script in client_scripts:
			doctype = script.get("dt") or ""
			if not doctype:
				continue
			behavior_graph.setdefault(doctype, []).append(
				{
					"type": "client_script",
					"event": script.get("view") or "form",
					"name": script.get("name"),
					"enabled": script.get("enabled"),
				}
			)

		for method, api_row in api_map.items():
			doctype = api_row.get("doctype") or _infer_doctype_from_method(method, semantic_registry)
			if not doctype:
				continue
			api_row["doctype"] = doctype
			behavior_graph.setdefault(doctype, []).append(
				{
					"type": "api",
					"method": method,
					"action": api_row.get("action") or "custom",
				}
			)
		return behavior_graph, rule_set

	def _persist_registry(self, registry: CustomizationRegistry) -> None:
		registry_dir = Path(frappe.get_site_path("private", "files", "intent_layer"))
		registry_dir.mkdir(parents=True, exist_ok=True)
		registry_path = registry_dir / self.REGISTRY_FILE
		registry_path.write_text(json.dumps(registry.to_dict(), indent=2, default=str), encoding="utf-8")

		settings = frappe.get_single("MCP Settings")
		settings.intent_layer_customization_path = str(registry_path)
		settings.intent_layer_customization_checksum = registry.checksum
		settings.intent_layer_customization_refresh = registry.refreshed_at
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _checksum_registry(self, payload: dict[str, Any]) -> str:
		raw = json.dumps(payload, sort_keys=True, default=str)
		return hashlib.sha256(raw.encode("utf-8")).hexdigest()

	def _boost_semantic_candidates(
		self,
		semantic_payload: dict[str, Any],
		customization_registry: CustomizationRegistry,
	) -> dict[str, Any]:
		payload = dict(semantic_payload or {})
		intent = payload.get("intent") or {}
		query_terms = [
			str(candidate)
			for candidate in intent.get("target_candidates") or []
			if candidate
		]
		query_terms.extend(
			str(value)
			for value in (intent.get("entities") or {}).values()
			if isinstance(value, str) and value
		)
		normalized_query = _normalize_text(" ".join(query_terms))
		if not normalized_query:
			return payload

		candidates = list(payload.get("candidates") or [])
		scores = {
			row.get("doctype"): float(row.get("score") or 0.0)
			for row in candidates
			if row.get("doctype")
		}
		candidate_payloads = {
			row.get("doctype"): dict(row)
			for row in candidates
			if row.get("doctype")
		}

		for doctype, aliases in self._customization_aliases(customization_registry).items():
			boost = 0.0
			for alias in aliases:
				score = _lexical_score(normalized_query, _normalize_text(alias))
				if score > boost:
					boost = score
			if boost < 0.2:
				continue
			scores[doctype] = max(scores.get(doctype, 0.0), min(0.97, 0.55 + boost / 2))
			candidate_payloads.setdefault(
				doctype,
				{
					"doctype": doctype,
					"fields": {},
					"workflow": {},
					"permissions": [],
					"relationships": [],
				},
			)

		payload["candidates"] = [
			{
				**candidate_payloads[doctype],
				"doctype": doctype,
				"score": round(score, 4),
			}
			for doctype, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
		][:8]
		payload["confidence"] = float(payload["candidates"][0]["score"]) if payload["candidates"] else 0.0
		return payload

	def _customization_aliases(
		self,
		registry: CustomizationRegistry,
	) -> dict[str, set[str]]:
		aliases: dict[str, set[str]] = {}

		for doctype, payload in (registry.custom_doctypes or {}).items():
			aliases.setdefault(doctype, set()).update(
				{
					doctype,
					payload.get("description") or "",
					payload.get("module") or "",
				}
			)
			for field in payload.get("fields") or []:
				aliases[doctype].update(
					{
						field.get("fieldname") or "",
						field.get("label") or "",
						field.get("options") or "",
					}
				)

		for doctype, rows in (registry.custom_fields or {}).items():
			aliases.setdefault(doctype, set())
			for row in rows:
				aliases[doctype].update(
					{
						row.get("fieldname") or "",
						row.get("label") or "",
						row.get("options") or "",
					}
				)

		for doctype, controller in (registry.controllers or {}).items():
			aliases.setdefault(doctype, set()).update(
				{
					str(controller.get("class_name") or ""),
					str(controller.get("path") or ""),
				}
			)
			for fn_name in controller.get("whitelisted_methods") or []:
				aliases[doctype].add(str(fn_name))
			for rule in controller.get("rules") or []:
				aliases[doctype].update(
					{
						str(rule.get("event") or ""),
						str(rule.get("condition") or ""),
						str(rule.get("action") or ""),
					}
				)

		for script in registry.server_scripts or []:
			doctype = script.get("reference_doctype") or ""
			if not doctype:
				continue
			aliases.setdefault(doctype, set()).update(
				{
					str(script.get("name") or ""),
					str(script.get("event") or ""),
					str(script.get("api_method") or ""),
					str(script.get("script_type") or ""),
				}
			)
			for rule in script.get("rules") or []:
				aliases[doctype].update(
					{
						str(rule.get("condition") or ""),
						str(rule.get("action") or ""),
					}
				)

		for script in registry.client_scripts or []:
			doctype = script.get("dt") or ""
			if not doctype:
				continue
			aliases.setdefault(doctype, set()).update(
				{
					str(script.get("name") or ""),
					str(script.get("view") or ""),
				}
			)

		for method, row in (registry.api_map or {}).items():
			doctype = row.get("doctype") or ""
			if not doctype:
				continue
			aliases.setdefault(doctype, set()).update(
				{
					str(method),
					str(row.get("function") or ""),
					str(row.get("module") or ""),
					str(row.get("action") or ""),
				}
			)

		for doctype, rows in (registry.behavior_graph or {}).items():
			aliases.setdefault(doctype, set())
			for row in rows or []:
				aliases[doctype].update(str(value or "") for value in row.values())

		return {
			doctype: {alias for alias in values if alias and _normalize_text(alias)}
			for doctype, values in aliases.items()
		}


def _infer_action_from_method(method_name: str) -> str:
	value = (method_name or "").lower()
	if any(token in value for token in ("create", "make", "new", "insert")):
		return "create"
	if any(token in value for token in ("update", "set", "edit", "modify")):
		return "update"
	if any(token in value for token in ("delete", "remove")):
		return "delete"
	if any(token in value for token in ("submit", "approve", "workflow", "transition", "reject")):
		return "workflow"
	if any(token in value for token in ("pay", "payment")):
		return "pay"
	if any(token in value for token in ("get", "fetch", "list", "search")):
		return "read"
	return "custom"


def _infer_doctype_from_method(method: str, semantic_registry: SemanticRegistry) -> str:
	normalized = re.sub(r"[^a-z0-9]+", " ", (method or "").lower()).strip()
	for doctype in semantic_registry.doctypes:
		candidate = re.sub(r"[^a-z0-9]+", " ", doctype.lower()).strip()
		if candidate and candidate in normalized:
			return doctype
	return ""


def _available_fields(doctype: str, candidates: list[str]) -> list[str]:
	try:
		meta = frappe.get_meta(doctype)
		available = {field.fieldname for field in meta.fields}
		available.add("name")
		return [fieldname for fieldname in candidates if fieldname in available]
	except Exception:
		return ["name"]


def _normalize_text(value: str) -> str:
	return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()


def _lexical_score(query: str, candidate: str) -> float:
	query = _normalize_text(query)
	candidate = _normalize_text(candidate)
	if not query or not candidate:
		return 0.0
	if query == candidate:
		return 1.0
	if query in candidate or candidate in query:
		shorter = min(len(query), len(candidate))
		longer = max(len(query), len(candidate))
		return min(0.95, 0.55 + shorter / max(longer, 1))
	query_tokens = set(query.split())
	candidate_tokens = set(candidate.split())
	if not query_tokens or not candidate_tokens:
		return 0.0
	return len(query_tokens & candidate_tokens) / len(query_tokens | candidate_tokens)
