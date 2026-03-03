"""
AI Chat Streaming Endpoint
SSE streaming chat endpoint for Vercel AI SDK useChat().
"""
import frappe
from werkzeug.wrappers import Response

from mcp_ui.ai.stream import STREAM_HEADERS


@frappe.whitelist(methods=["POST"])
def stream():
	"""
	SSE streaming chat endpoint for Vercel AI SDK useChat().

	Accepts both formats:
	  - Simple: {"messages": [{"role": "user", "content": "..."}]}
	  - AI SDK v6 UIMessage: {"messages": [{"role": "user", "parts": [{"type": "text", "text": "..."}]}]}

	Returns: Data Stream Protocol v1 (text/plain SSE)
	"""
	from mcp_ui.ai.engine import stream_chat

	data = frappe.request.get_json(force=True)
	raw_messages = data.get("messages", [])
	user = frappe.session.user

	# Normalize messages: AI SDK v6 sends UIMessage with parts[], litellm needs {role, content}
	messages = []
	for msg in raw_messages:
		role = msg.get("role", "user")

		# If it already has "content" as a string, use it directly
		if isinstance(msg.get("content"), str):
			messages.append({"role": role, "content": msg["content"]})
			continue

		# AI SDK v6 UIMessage format: parts array with {type: "text", text: "..."}
		parts = msg.get("parts", [])
		if parts:
			text_parts = [p.get("text", "") for p in parts if p.get("type") == "text"]
			content = "\n".join(text_parts).strip()
			if content:
				messages.append({"role": role, "content": content})
			continue

		# Fallback: skip messages with no content
		if msg.get("content"):
			messages.append({"role": role, "content": str(msg["content"])})

	def generate():
		for chunk in stream_chat(messages, user):
			yield chunk

	response = Response(generate(), content_type="text/plain; charset=utf-8")
	for key, value in STREAM_HEADERS.items():
		response.headers[key] = value

	return response
