"""
MCP Tools API
Provides endpoints for tool discovery and execution
"""
import json

import frappe


@frappe.whitelist()
def get_available_tools():
	"""
	Get list of all available MCP tools with their metadata
	"""
	# Import to ensure tools are registered
	from mcp_ui.mcp_server import mcp

	# Get registered tools from MCP instance
	tools = []

	# Core tools metadata
	core_tools_meta = [
		{
			"name": "create_document",
			"title": "Create Document",
			"description": "Create a new document in Frappe",
			"category": "CRUD",
			"base_cost": 3,
			"destructive": False,
			"read_only": False,
		},
		{
			"name": "update_document",
			"title": "Update Document",
			"description": "Update an existing document",
			"category": "CRUD",
			"base_cost": 2,
			"destructive": False,
			"read_only": False,
		},
		{
			"name": "delete_document",
			"title": "Delete Document",
			"description": "Delete a document from Frappe",
			"category": "CRUD",
			"base_cost": 2,
			"destructive": True,
			"read_only": False,
		},
		{
			"name": "get_document",
			"title": "Get Document",
			"description": "Fetch a single document",
			"category": "CRUD",
			"base_cost": 1,
			"destructive": False,
			"read_only": True,
		},
		{
			"name": "get_list",
			"title": "Get List",
			"description": "Get a list of documents with filters",
			"category": "Query",
			"base_cost": 1,
			"destructive": False,
			"read_only": True,
		},
		{
			"name": "search_documents",
			"title": "Search Documents",
			"description": "Search documents by text",
			"category": "Query",
			"base_cost": 2,
			"destructive": False,
			"read_only": True,
		},
		{
			"name": "execute_report",
			"title": "Execute Report",
			"description": "Run a Frappe report",
			"category": "Reports",
			"base_cost": 5,
			"destructive": False,
			"read_only": True,
		},
		{
			"name": "bulk_update",
			"title": "Bulk Update",
			"description": "Update multiple documents at once",
			"category": "Bulk",
			"base_cost": 10,
			"destructive": False,
			"read_only": False,
		},
		{
			"name": "export_data",
			"title": "Export Data",
			"description": "Export data in JSON format",
			"category": "Export",
			"base_cost": 5,
			"destructive": False,
			"read_only": True,
		},
		{
			"name": "get_dashboard_data",
			"title": "Get Dashboard Data",
			"description": "Get dashboard statistics",
			"category": "Analytics",
			"base_cost": 2,
			"destructive": False,
			"read_only": True,
		},
	]

	return {"success": True, "tools": core_tools_meta, "count": len(core_tools_meta)}


@frappe.whitelist()
def execute_tool(tool_name, params):
	"""
	Execute an MCP tool with credit tracking

	Args:
		tool_name: Name of the tool to execute
		params: Tool parameters as JSON string or dict

	Returns:
		Tool execution result
	"""
	# Parse params if string
	if isinstance(params, str):
		try:
			params = json.loads(params)
		except json.JSONDecodeError:
			frappe.throw("Invalid parameters format")

	# Import tool functions
	from mcp_ui.mcp_server import core_tools

	# Map tool names to functions
	tool_functions = {
		"create_document": core_tools.create_document,
		"update_document": core_tools.update_document,
		"delete_document": core_tools.delete_document,
		"get_document": core_tools.get_document,
		"get_list": core_tools.get_list,
		"search_documents": core_tools.search_documents,
		"execute_report": core_tools.execute_report,
		"bulk_update": core_tools.bulk_update,
		"export_data": core_tools.export_data,
		"get_dashboard_data": core_tools.get_dashboard_data,
	}

	# Get tool function
	tool_func = tool_functions.get(tool_name)

	if not tool_func:
		frappe.throw(f"Tool '{tool_name}' not found")

	# Execute tool
	try:
		result = tool_func(**params)

		# Log successful execution
		from mcp_ui.api.credits import get_balance

		balance = get_balance()

		return {
			"success": True,
			"result": result,
			"tool": tool_name,
			"remaining_credits": balance.get("balance", 0),
		}

	except Exception as e:
		frappe.log_error(f"Tool execution failed: {tool_name}", str(e))
		frappe.throw(f"Tool execution failed: {str(e)}")


@frappe.whitelist()
def get_tool_schema(tool_name):
	"""
	Get the input schema for a specific tool

	Args:
		tool_name: Name of the tool

	Returns:
		JSON schema for tool inputs
	"""
	# Define schemas for each tool
	schemas = {
		"create_document": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name (e.g., 'Customer')"},
				"data": {"type": "object", "description": "Field values as key-value pairs"},
			},
			"required": ["doctype", "data"],
		},
		"update_document": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"name": {"type": "string", "description": "Document ID"},
				"data": {"type": "object", "description": "Fields to update"},
			},
			"required": ["doctype", "name", "data"],
		},
		"delete_document": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"name": {"type": "string", "description": "Document ID"},
			},
			"required": ["doctype", "name"],
		},
		"get_document": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"name": {"type": "string", "description": "Document ID"},
			},
			"required": ["doctype", "name"],
		},
		"get_list": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"filters": {"type": "object", "description": "Filter conditions"},
				"fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to fetch"},
				"limit": {"type": "integer", "default": 20, "description": "Max records"},
			},
			"required": ["doctype"],
		},
		"search_documents": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"search_text": {"type": "string", "description": "Text to search"},
				"limit": {"type": "integer", "default": 20, "description": "Max results"},
			},
			"required": ["doctype", "search_text"],
		},
		"execute_report": {
			"type": "object",
			"properties": {
				"report_name": {"type": "string", "description": "Report name"},
				"filters": {"type": "object", "description": "Report filters"},
			},
			"required": ["report_name"],
		},
		"bulk_update": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"filters": {"type": "object", "description": "Filter to select documents"},
				"update_data": {"type": "object", "description": "Fields to update"},
			},
			"required": ["doctype", "filters", "update_data"],
		},
		"export_data": {
			"type": "object",
			"properties": {
				"doctype": {"type": "string", "description": "DocType name"},
				"filters": {"type": "object", "description": "Filter conditions"},
				"fields": {"type": "array", "items": {"type": "string"}},
				"limit": {"type": "integer", "default": 100},
			},
			"required": ["doctype"],
		},
		"get_dashboard_data": {
			"type": "object",
			"properties": {"doctype": {"type": "string", "description": "DocType name"}},
			"required": ["doctype"],
		},
	}

	schema = schemas.get(tool_name)

	if not schema:
		frappe.throw(f"Schema not found for tool: {tool_name}")

	return {"success": True, "tool": tool_name, "schema": schema}

