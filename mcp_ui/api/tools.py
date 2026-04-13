"""
Unified action discovery and execution API for MCP UI and OpenClaw.
"""
from __future__ import annotations

import json

import frappe

from mcp_ui.openclaw.actions import execute_action, get_action_catalog
from mcp_ui.openclaw.federation import execute_as_mapped_user


@frappe.whitelist()
def get_available_tools():
	actions = get_action_catalog()
	return {"success": True, "tools": actions, "count": len(actions)}


@frappe.whitelist()
def execute_tool(tool_name, params=None, session_context=None, validate_only: int = 0):
	if isinstance(params, str):
		params = json.loads(params)
	if isinstance(session_context, str):
		session_context = json.loads(session_context)

	params = params or {}
	session_context = session_context or {}

	try:
		if session_context:
			result = execute_as_mapped_user(
				session_context=session_context,
				action=tool_name,
				args=params,
				validate_only=bool(int(validate_only)),
			)
			return {"success": result.get("success"), "result": result, "tool": tool_name}

		result = execute_action(tool_name, params)
		return {"success": True, "result": result, "tool": tool_name}
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Tool execution failed")
		frappe.throw(f"Tool execution failed: {str(exc)}")


@frappe.whitelist()
def get_tool_schema(tool_name):
	from mcp_ui.ai.tools import get_tool_schemas

	for schema in get_tool_schemas():
		function = schema.get("function", {})
		if function.get("name") == tool_name:
			return {"success": True, "schema": function.get("parameters"), "tool": tool_name}

	extra = next((entry for entry in get_action_catalog() if entry["name"] == tool_name), None)
	if extra:
		return {
			"success": True,
			"schema": {"type": "object", "properties": {}},
			"tool": tool_name,
			"note": "Schema is dynamic for non-AI action endpoints.",
		}

	frappe.throw(f"Tool '{tool_name}' not found")

