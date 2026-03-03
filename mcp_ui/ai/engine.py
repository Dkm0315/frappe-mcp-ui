"""
Core AI Chat Engine
Handles: LLM call → tool execution → multi-step loop → streaming via UI Message Stream Protocol.
Supports up to 25 tool-calling rounds per message for complex business processes.
"""
import json
import traceback

import frappe
import litellm

from mcp_ui.ai.providers import get_provider_config, get_system_prompt
from mcp_ui.ai.tools import get_tool_schemas, get_tool_map
from mcp_ui.ai.stream import (
	start_message,
	start_step,
	text_start,
	text_delta,
	text_end,
	tool_input_start,
	tool_input_available,
	tool_output_available,
	tool_output_error,
	error_event,
	finish_step,
	finish_message,
	generate_id,
)


def stream_chat(messages: list, user: str):
	"""
	Main streaming chat function.
	Yields UI Message Stream protocol chunks for useChat().

	Args:
		messages: List of {role, content} message dicts
		user: Frappe user email (session.user)

	Yields:
		SSE formatted strings (data: {JSON}\n\n)
	"""
	config = get_provider_config()

	if not config.get("enabled"):
		yield error_event("AI chat is not enabled. Go to MCP Settings to configure it.")
		yield finish_message()
		return

	# Build the LLM call kwargs
	model = config["model"]
	llm_kwargs = {"model": model, "stream": True}

	if config.get("api_key"):
		llm_kwargs["api_key"] = config["api_key"]
	if config.get("api_base"):
		llm_kwargs["api_base"] = config["api_base"]

	# Build messages with system prompt
	system_prompt = get_system_prompt()
	llm_messages = [{"role": "system", "content": system_prompt}]
	llm_messages.extend(messages)

	# Get tool definitions
	tool_schemas = get_tool_schemas()
	tool_map = get_tool_map()
	max_steps = config.get("max_steps", 25)

	# Start the message
	yield start_message()

	# Multi-step tool calling loop
	for step in range(max_steps):
		yield start_step()

		try:
			# Call LLM with streaming
			response = litellm.completion(
				messages=llm_messages,
				tools=tool_schemas if tool_schemas else None,
				**llm_kwargs,
			)

			# Collect the streamed response
			collected_content = ""
			collected_tool_calls = []
			text_id = generate_id()
			text_started = False

			for chunk in response:
				delta = chunk.choices[0].delta if chunk.choices else None
				if not delta:
					continue

				# Stream text content
				if delta.content:
					if not text_started:
						yield text_start(text_id)
						text_started = True
					collected_content += delta.content
					yield text_delta(text_id, delta.content)

				# Collect tool calls
				if delta.tool_calls:
					for tc in delta.tool_calls:
						if tc.index is not None:
							while len(collected_tool_calls) <= tc.index:
								collected_tool_calls.append({
									"id": "",
									"function": {"name": "", "arguments": ""},
								})

							if tc.id:
								collected_tool_calls[tc.index]["id"] = tc.id
							if tc.function:
								if tc.function.name:
									collected_tool_calls[tc.index]["function"]["name"] = tc.function.name
								if tc.function.arguments:
									collected_tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

			# End text part if we started one
			if text_started:
				yield text_end(text_id)

			# If no tool calls, we're done
			if not collected_tool_calls:
				yield finish_step()
				yield finish_message()
				return

			# Execute tool calls
			# Add assistant message with tool calls to context
			assistant_msg = {"role": "assistant", "content": collected_content or None}
			assistant_msg["tool_calls"] = [
				{
					"id": tc["id"],
					"type": "function",
					"function": {
						"name": tc["function"]["name"],
						"arguments": tc["function"]["arguments"],
					},
				}
				for tc in collected_tool_calls
			]
			llm_messages.append(assistant_msg)

			# Execute each tool call
			for tc in collected_tool_calls:
				tool_name = tc["function"]["name"]
				tool_call_id = tc["id"]

				try:
					args = json.loads(tc["function"]["arguments"])
				except json.JSONDecodeError:
					args = {}

				# Emit tool input events
				yield tool_input_start(tool_call_id, tool_name)
				yield tool_input_available(tool_call_id, tool_name, args)

				# Execute the tool
				tool_fn = tool_map.get(tool_name)
				if not tool_fn:
					result = {"error": f"Unknown tool: {tool_name}"}
					yield tool_output_error(tool_call_id, f"Unknown tool: {tool_name}")
				else:
					try:
						frappe.set_user(user)
						result = tool_fn(**args)
						yield tool_output_available(tool_call_id, result)
					except frappe.PermissionError as e:
						result = {"error": f"Permission denied: {str(e)}"}
						yield tool_output_error(tool_call_id, f"Permission denied: {str(e)}")
					except PermissionError as e:
						result = {"error": str(e)}
						yield tool_output_error(tool_call_id, str(e))
					except Exception as e:
						result = {"error": f"Tool execution failed: {str(e)}"}
						yield tool_output_error(tool_call_id, f"Tool execution failed: {str(e)}")

				# Log the tool usage
				_log_usage(user, tool_name, args, result)

				# Add tool result to messages for next LLM call
				llm_messages.append({
					"role": "tool",
					"tool_call_id": tool_call_id,
					"content": json.dumps(result, default=str),
				})

			# End this step, continue to next
			yield finish_step()

		except Exception as e:
			error_msg = f"AI engine error: {str(e)}"
			frappe.log_error(traceback.format_exc(), "AI Chat Engine Error")
			yield error_event(error_msg)
			yield finish_step()
			yield finish_message()
			return

	# If we exhausted all steps
	text_id = generate_id()
	yield text_start(text_id)
	yield text_delta(text_id, "\n\n[Reached maximum tool-calling steps. The operation may be partially complete.]")
	yield text_end(text_id)
	yield finish_step()
	yield finish_message()


def _log_usage(user: str, tool_name: str, args: dict, result: dict):
	"""Log AI tool usage to MCP Usage Log."""
	try:
		frappe.get_doc({
			"doctype": "MCP Usage Log",
			"user": user,
			"tool_name": tool_name,
			"parameters": json.dumps(args, default=str)[:2000],
			"result_summary": json.dumps(result, default=str)[:2000],
			"source": "ai_chat",
		}).insert(ignore_permissions=True)
	except Exception:
		pass
