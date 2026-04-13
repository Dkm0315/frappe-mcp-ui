from __future__ import annotations

from typing import Any, Callable

import frappe


ActionFn = Callable[..., Any]


PRIMITIVE_ACTIONS = {
	"get_list",
	"get_document",
	"create_document",
	"update_document",
	"delete_document",
	"search_documents",
	"submit_document",
	"cancel_document",
	"amend_document",
	"make_mapped_document",
	"bulk_create",
	"bulk_update",
	"bulk_delete",
}


def _ai_actions() -> dict[str, ActionFn]:
	from mcp_ui.ai.tools import get_tool_map

	return get_tool_map()


def _extra_actions() -> dict[str, ActionFn]:
	from mcp_ui.api import discovery, form_builder, ide, workflow_integration

	return {
		"discovery.get_installed_apps": discovery.get_installed_apps,
		"discovery.get_doctypes": discovery.get_doctypes,
		"discovery.get_custom_fields": discovery.get_custom_fields,
		"discovery.get_workflows": discovery.get_workflows,
		"discovery.get_doctype_meta": discovery.get_doctype_meta,
		"discovery.get_system_stats": discovery.get_system_stats,
		"discovery.get_doctypes_by_module": discovery.get_doctypes_by_module,
		"form.get_doctype_form_fields": form_builder.get_doctype_form_fields,
		"form.search_link_field": form_builder.search_link_field,
		"form.get_quick_create_templates": form_builder.get_quick_create_templates,
		"ide.get_capabilities": ide.get_capabilities,
		"ide.get_client_scripts": ide.get_client_scripts,
		"ide.get_client_script": ide.get_client_script,
		"ide.save_client_script": ide.save_client_script,
		"ide.delete_client_script": ide.delete_client_script,
		"ide.get_server_scripts": ide.get_server_scripts,
		"ide.get_server_script": ide.get_server_script,
		"ide.save_server_script": ide.save_server_script,
		"ide.delete_server_script": ide.delete_server_script,
		"ide.get_frappe_workflows": ide.get_frappe_workflows,
		"ide.save_workflow": ide.save_workflow,
		"ide.delete_workflow": ide.delete_workflow,
		"ide.get_custom_fields_for_doctype": ide.get_custom_fields_for_doctype,
		"ide.add_custom_field": ide.add_custom_field,
		"ide.delete_custom_field": ide.delete_custom_field,
		"ide.get_property_setters": ide.get_property_setters,
		"ide.set_property": ide.set_property,
		"ide.get_notifications": ide.get_notifications,
		"ide.get_notification": ide.get_notification,
		"ide.get_doc_events": ide.get_doc_events,
		"workflow.get_workflows": workflow_integration.get_workflows,
		"workflow.trigger_workflow": workflow_integration.trigger_workflow,
		"workflow.get_workflow_status": workflow_integration.get_workflow_status,
		"workflow.get_builder_url": workflow_integration.get_builder_url,
		"workflow.get_workflow_definition": workflow_integration.get_workflow_definition,
		"workflow.create_funnel": workflow_integration.create_funnel,
		"workflow.update_funnel": workflow_integration.update_funnel,
	}


def get_action_map() -> dict[str, ActionFn]:
	actions = {}
	actions.update(_ai_actions())
	actions.update(_extra_actions())
	return actions


def get_action_metadata(name: str) -> dict[str, Any]:
	category = "tool"
	if "." in name:
		category = name.split(".", 1)[0]

	aliases: list[str] = []
	mode_required = "normal"
	execution_path = "server"
	surface = "primitive" if name in PRIMITIVE_ACTIONS else "capability"

	if name == "get_list":
		aliases = ["list documents", "show records", "find records", "document inventory"]
	elif name == "get_document":
		aliases = ["open record", "show document", "fetch document"]
	elif name == "get_form_guidance":
		aliases = ["create form", "required fields", "ask missing details", "document intake"]
	elif name == "run_report":
		aliases = ["report data", "report rows", "analytics report", "summary report", "sla report"]
	elif name == "create_document":
		aliases = ["create record", "create document", "submit new request"]
	elif name == "update_document":
		aliases = ["edit record", "change document", "update record"]
	elif name == "form.search_link_field":
		aliases = ["search link option", "find valid option", "lookup linked record"]
	elif name == "workflow.trigger_workflow":
		aliases = ["approve workflow", "reject workflow", "transition workflow", "workflow action"]
	elif name == "workflow.create_funnel":
		aliases = ["create funnel", "build funnel", "nextai funnel setup"]
	elif name == "workflow.update_funnel":
		aliases = ["update funnel", "edit funnel", "change funnel"]
	elif name.startswith("ide."):
		aliases = ["customize system", "script change", "custom field", "workflow design", "property setter"]

	write_tokens = ("create", "update", "save", "delete", "submit", "cancel", "amend", "set_", "add_", "remove_", "trigger")
	write = any(token in name for token in write_tokens)
	if name in {"bulk_create", "bulk_update", "bulk_delete", "create_document", "update_document", "delete_document"}:
		write = True
	destructive = any(token in name for token in ("delete", "cancel"))

	if name.startswith("ide.") and write:
		mode_required = "admin"
	if name.startswith("workflow.") and write and name not in {"workflow.trigger_workflow"}:
		mode_required = "admin"
	if name.startswith("form."):
		execution_path = "ui"

	return {
		"name": name,
		"category": category,
		"aliases": aliases,
		"destructive": destructive,
		"write": write,
		"mode_required": mode_required,
		"execution_path": execution_path,
		"surface": surface,
	}


def get_action_catalog() -> list[dict[str, Any]]:
	catalog = []
	action_map = get_action_map()
	for name in sorted(action_map):
		fn = action_map[name]
		description = ""
		schema = getattr(fn, "_schema", None)
		if isinstance(schema, dict):
			description = schema.get("description", "") or ""
		metadata = get_action_metadata(name)
		catalog.append(
			{
				"name": name,
				"category": metadata["category"],
				"description": description,
				"aliases": metadata["aliases"],
				"destructive": metadata["destructive"],
				"write": metadata["write"],
				"mode_required": metadata["mode_required"],
				"execution_path": metadata["execution_path"],
				"surface": metadata["surface"],
			}
		)

	return catalog


def execute_action(action: str, args: dict[str, Any] | None = None) -> Any:
	fn = get_action_map().get(action)
	if not fn:
		frappe.throw(f"Unknown action: {action}")

	return fn(**(args or {}))
