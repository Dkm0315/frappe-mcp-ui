"""
UI Message Stream Protocol for Vercel AI SDK v6
Implements the SSE-based UI message stream protocol so useChat() works on the frontend.

Format: Each event is `data: {JSON}\n\n` (standard SSE)

Chunk types:
  start             — start of message
  start-step        — start of a step (each LLM call is a step)
  text-start        — begin a text part
  text-delta        — text chunk
  text-end          — end text part
  tool-input-start  — tool call begin
  tool-input-available — tool call with full input
  tool-output-available — tool result
  finish-step       — end of step
  finish            — end of message

Headers required:
  x-vercel-ai-ui-message-stream: v1
  Content-Type: text/event-stream
"""
import json
import uuid


def _sse(data: dict) -> str:
	"""Format a single SSE event."""
	return f"data: {json.dumps(data, default=str)}\n\n"


def start_message(message_id: str = None) -> str:
	"""Signal start of a new assistant message."""
	payload = {"type": "start"}
	if message_id:
		payload["messageId"] = message_id
	return _sse(payload)


def start_step() -> str:
	"""Signal start of a step (each LLM call = 1 step)."""
	return _sse({"type": "start-step"})


def text_start(text_id: str) -> str:
	"""Begin a text part."""
	return _sse({"type": "text-start", "id": text_id})


def text_delta(text_id: str, delta: str) -> str:
	"""Stream a text chunk."""
	return _sse({"type": "text-delta", "id": text_id, "delta": delta})


def text_end(text_id: str) -> str:
	"""End a text part."""
	return _sse({"type": "text-end", "id": text_id})


def tool_input_start(tool_call_id: str, tool_name: str) -> str:
	"""Signal start of a tool call."""
	return _sse({
		"type": "tool-input-start",
		"toolCallId": tool_call_id,
		"toolName": tool_name,
	})


def tool_input_available(tool_call_id: str, tool_name: str, input_data: dict) -> str:
	"""Emit the full tool call input."""
	return _sse({
		"type": "tool-input-available",
		"toolCallId": tool_call_id,
		"toolName": tool_name,
		"input": input_data,
	})


def tool_output_available(tool_call_id: str, output: dict) -> str:
	"""Emit a tool result."""
	return _sse({
		"type": "tool-output-available",
		"toolCallId": tool_call_id,
		"output": output,
	})


def tool_output_error(tool_call_id: str, error_text: str) -> str:
	"""Emit a tool error."""
	return _sse({
		"type": "tool-output-error",
		"toolCallId": tool_call_id,
		"errorText": error_text,
	})


def error_event(error_text: str) -> str:
	"""Emit an error event."""
	return _sse({"type": "error", "errorText": error_text})


def finish_step() -> str:
	"""Signal end of a step."""
	return _sse({"type": "finish-step"})


def finish_message() -> str:
	"""Signal end of the message."""
	return _sse({"type": "finish"})


def generate_id() -> str:
	"""Generate a unique ID."""
	return uuid.uuid4().hex[:24]


STREAM_HEADERS = {
	"Content-Type": "text/event-stream",
	"Cache-Control": "no-cache",
	"Connection": "keep-alive",
	"X-Vercel-AI-UI-Message-Stream": "v1",
	"X-Accel-Buffering": "no",
}
