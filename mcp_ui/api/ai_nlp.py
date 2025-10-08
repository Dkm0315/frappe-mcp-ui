"""
AI-Enhanced Natural Language Processing
Uses OpenAI Function Calling for better tool mapping
"""
import json
import frappe
from mcp_ui.utils.app_checker import get_openai_api_key, get_anthropic_api_key


@frappe.whitelist()
def parse_with_ai(query):
	"""
	Parse natural language using OpenAI Function Calling
	
	Args:
		query: User's natural language query
		
	Returns:
		AI-enhanced suggestions with tool calls
	"""
	settings = frappe.get_single("MCP Settings")
	
	if not settings.enable_ai_nlp:
		# Fall back to basic NLP
		from mcp_ui.api.nlp_processor import parse_natural_language
		return parse_natural_language(query)
	
	provider = settings.ai_provider
	
	if provider == "OpenAI":
		return _parse_with_openai_tools(query, settings)
	elif provider == "Anthropic":
		return _parse_with_anthropic_tools(query, settings)
	else:
		# Fall back to basic NLP
		from mcp_ui.api.nlp_processor import parse_natural_language
		return parse_natural_language(query)


def _get_mcp_tool_definitions():
	"""Get MCP tools as OpenAI function definitions"""
	
	# Get available DocTypes for enum
	doctypes = frappe.get_all("DocType", filters={"istable": 0, "custom": 0}, pluck="name", limit=100)
	
	tools = [
		{
			"type": "function",
			"function": {
				"name": "create_document",
				"description": "Create a new document/record in the system. Use this when user wants to create, add, or insert new data.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document to create (e.g., Customer, Item, Sales Order)"
						}
					},
					"required": ["doctype"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "get_list",
				"description": "Get a list of documents. Use this when user wants to see, list, show, or view multiple records.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of documents to list"
						},
						"limit": {
							"type": "number",
							"description": "Maximum number of records to return",
							"default": 20
						}
					},
					"required": ["doctype"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "search_documents",
				"description": "Search for documents by text. Use this when user wants to find, search for, or look up specific records.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of documents to search"
						},
						"search_text": {
							"type": "string",
							"description": "The text to search for"
						},
						"limit": {
							"type": "number",
							"description": "Maximum number of results",
							"default": 20
						}
					},
					"required": ["doctype", "search_text"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "update_document",
				"description": "Update an existing document. Use this when user wants to modify, edit, change, or update a record.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document to update"
						},
						"name": {
							"type": "string",
							"description": "The ID or name of the document to update"
						}
					},
					"required": ["doctype", "name"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "delete_document",
				"description": "Delete a document. Use this when user wants to remove, delete, or discard a record. This is DESTRUCTIVE.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document to delete"
						},
						"name": {
							"type": "string",
							"description": "The ID or name of the document to delete"
						}
					},
					"required": ["doctype", "name"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "get_document",
				"description": "Get a single document by name/ID. Use this when user wants details about a specific record.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document"
						},
						"name": {
							"type": "string",
							"description": "The ID or name of the document"
						}
					},
					"required": ["doctype", "name"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "get_dashboard_data",
				"description": "Get dashboard statistics and overview for a DocType. Use when user wants stats, overview, dashboard, or summary.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document to get stats for"
						}
					},
					"required": ["doctype"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "bulk_create",
				"description": "Create multiple documents at once. Use when user wants to create many records in bulk.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of documents to create"
						},
						"count": {
							"type": "number",
							"description": "How many records user wants to create"
						}
					},
					"required": ["doctype"]
				}
			}
		},
		{
			"type": "function",
			"function": {
				"name": "export_data",
				"description": "Export data to file. Use when user wants to export, download, or extract data.",
				"parameters": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of documents to export"
						},
						"limit": {
							"type": "number",
							"description": "Maximum records to export",
							"default": 100
						}
					},
					"required": ["doctype"]
				}
			}
		}
	]
	
	return tools


def _parse_with_openai_tools(query, settings):
	"""Parse using OpenAI Function Calling"""
	try:
		import openai
		
		# Use app_checker to get API key with fallback
		api_key = get_openai_api_key()
		if not api_key:
			frappe.throw("OpenAI API key not configured in MCP Settings or ChatNext Settings")
		
		client = openai.OpenAI(api_key=api_key)
		
		# Get tool definitions
		tools = _get_mcp_tool_definitions()
		
		# Call OpenAI with function calling
		response = client.chat.completions.create(
			model=settings.openai_model or "gpt-4o-mini",
			messages=[
				{
					"role": "system",
					"content": "You are a helpful assistant that helps users interact with their Frappe ERP system. Parse the user's request and call the appropriate function."
				},
				{
					"role": "user",
					"content": query
				}
			],
			tools=tools,
			tool_choice="auto",
			temperature=0.3,
		)
		
		message = response.choices[0].message
		
		# Check if OpenAI wants to call a function
		if message.tool_calls:
			tool_call = message.tool_calls[0]
			function_name = tool_call.function.name
			function_args = json.loads(tool_call.function.arguments)
			
			# Map next step based on tool
			next_step = "execute"
			if function_name in ["create_document", "update_document", "bulk_create"]:
				next_step = "form"
			elif function_name == "delete_document":
				next_step = "confirm"
			
			# Determine if destructive
			is_destructive = function_name in ["delete_document", "bulk_delete"]
			
			return {
				"success": True,
				"query": query,
				"suggestions": [{
					"tool": function_name,
					"params": function_args,
					"confidence": "high",
					"description": f"{message.content or tool_call.function.name.replace('_', ' ').title()}",
					"next_step": next_step,
					"warning": "This is a destructive operation" if is_destructive else None
				}]
			}
		else:
			# No function call, return helpful message
			return {
				"success": True,
				"query": query,
				"suggestions": [{
					"confidence": "low",
					"message": message.content or "I didn't understand that. Could you rephrase?",
					"examples": [
						"Create a new customer",
						"Show all items",
						"Search for John in customers",
						"Get customer dashboard"
					]
				}]
			}
		
	except Exception as e:
		frappe.log_error(f"OpenAI Function Calling error: {str(e)}")
		# Fall back to basic NLP
		from mcp_ui.api.nlp_processor import parse_natural_language
		return parse_natural_language(query)


def _parse_with_anthropic_tools(query, settings):
	"""Parse using Anthropic Claude with Tool Use"""
	try:
		import anthropic
		
		# Use app_checker to get API key
		api_key = get_anthropic_api_key()
		if not api_key:
			frappe.throw("Anthropic API key not configured in MCP Settings")
		
		client = anthropic.Anthropic(api_key=api_key)
		
		# Get available DocTypes
		doctypes = frappe.get_all("DocType", filters={"istable": 0, "custom": 0}, pluck="name", limit=100)
		
		# Define tools for Anthropic
		tools = [
			{
				"name": "create_document",
				"description": "Create a new document/record in the system",
				"input_schema": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document to create"
						}
					},
					"required": ["doctype"]
				}
			},
			{
				"name": "get_list",
				"description": "Get a list of documents",
				"input_schema": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of documents to list"
						},
						"limit": {
							"type": "number",
							"description": "Maximum records to return",
							"default": 20
						}
					},
					"required": ["doctype"]
				}
			},
			{
				"name": "search_documents",
				"description": "Search for documents by text",
				"input_schema": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of documents to search"
						},
						"search_text": {
							"type": "string",
							"description": "The text to search for"
						}
					},
					"required": ["doctype", "search_text"]
				}
			},
			{
				"name": "get_dashboard_data",
				"description": "Get dashboard statistics for a DocType",
				"input_schema": {
					"type": "object",
					"properties": {
						"doctype": {
							"type": "string",
							"enum": doctypes,
							"description": "The type of document"
						}
					},
					"required": ["doctype"]
				}
			}
		]
		
		message = client.messages.create(
			model=settings.anthropic_model or "claude-3-5-haiku-20241022",
			max_tokens=1024,
			tools=tools,
			messages=[
				{
					"role": "user",
					"content": query
				}
			]
		)
		
		# Check for tool use
		for content in message.content:
			if content.type == "tool_use":
				tool_name = content.name
				tool_input = content.input
				
				# Map next step
				next_step = "execute"
				if tool_name in ["create_document", "update_document"]:
					next_step = "form"
				elif tool_name == "delete_document":
					next_step = "confirm"
				
				return {
					"success": True,
					"query": query,
					"suggestions": [{
						"tool": tool_name,
						"params": tool_input,
						"confidence": "high",
						"description": tool_name.replace('_', ' ').title(),
						"next_step": next_step
					}]
				}
		
		# No tool use, return text response
		return {
			"success": True,
			"query": query,
			"suggestions": [{
				"confidence": "low",
				"message": message.content[0].text if message.content else "I didn't understand that.",
				"examples": [
					"Create a new customer",
					"Show all items",
					"Search for John in customers"
				]
			}]
		}
		
	except Exception as e:
		frappe.log_error(f"Anthropic Tool Use error: {str(e)}")
		# Fall back to basic NLP
		from mcp_ui.api.nlp_processor import parse_natural_language
		return parse_natural_language(query)

