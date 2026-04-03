"""Adapter that treats OpenClaw as the execution runtime boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mcp_ui.intent_layer.tools import execute_tool_call
from mcp_ui.openclaw.manager import ensure_gateway_running, get_status


class OpenClawAdapter:
	"""Dispatch validated planner steps through the OpenClaw runtime boundary."""

	GATEWAY_URL = "http://127.0.0.1:18789/tools/invoke"
	GATEWAY_SERVER_PREFIX = "frappe"
	REQUEST_TIMEOUT = 30

	def health(self) -> dict[str, Any]:
		status = get_status()
		return {
			"enabled": bool(status.get("enabled")),
			"installed": bool(status.get("installed")),
			"running": bool(status.get("running")),
			"has_config": bool(status.get("has_config")),
			"pid": status.get("pid"),
			"log_file": status.get("log_file"),
			"config_file": status.get("config_file"),
			"runtime": "openclaw_gateway" if status.get("running") else "local_fallback",
		}

	def execute(self, tool: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
		params = params or {}
		status = self._ensure_gateway_status()
		if status.get("enabled") and status.get("running") and status.get("has_config"):
			gateway_result = self._invoke_gateway_tool(
				tool=tool,
				params=params,
				config_file=str(status.get("config_file") or ""),
			)
			if gateway_result.get("status") == "success":
				return gateway_result
			if not self._should_use_local_fallback(gateway_result):
				return gateway_result

		try:
			data = execute_tool_call(tool, params)
			return {
				"status": "success",
				"data": data,
				"error": None,
				"runtime": "local_fallback",
			}
		except Exception as exc:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": type(exc).__name__,
					"message": str(exc),
				},
				"runtime": "local_fallback",
			}

	def _ensure_gateway_status(self) -> dict[str, Any]:
		status = get_status()
		if status.get("enabled") and not status.get("running"):
			ensure_gateway_running()
			status = get_status()
		return status

	def _invoke_gateway_tool(
		self,
		tool: str,
		params: dict[str, Any],
		config_file: str,
	) -> dict[str, Any]:
		token = self._read_gateway_token(config_file)
		if not token:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawConfigError",
					"message": "OpenClaw gateway token is missing from openclaw.json.",
				},
				"runtime": "openclaw_gateway",
			}

		payload = json.dumps(
			{
				"id": f"{self.GATEWAY_SERVER_PREFIX}_{tool}",
				"args": params,
			}
		).encode("utf-8")
		request = Request(
			self.GATEWAY_URL,
			data=payload,
			headers={
				"Authorization": f"Bearer {token}",
				"Content-Type": "application/json",
			},
			method="POST",
		)
		try:
			with urlopen(request, timeout=self.REQUEST_TIMEOUT) as response:
				raw_payload = response.read().decode("utf-8")
		except HTTPError as exc:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawTransportError",
					"message": f"OpenClaw gateway HTTP {exc.code}: {exc.reason}",
				},
				"runtime": "openclaw_gateway",
			}
		except URLError as exc:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawTransportError",
					"message": f"OpenClaw gateway is unreachable: {exc.reason}",
				},
				"runtime": "openclaw_gateway",
			}
		except TimeoutError as exc:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawTimeoutError",
					"message": f"OpenClaw gateway timed out after {self.REQUEST_TIMEOUT}s: {exc}",
				},
				"runtime": "openclaw_gateway",
			}
		except Exception as exc:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": type(exc).__name__,
					"message": str(exc),
				},
				"runtime": "openclaw_gateway",
			}

		try:
			gateway_payload = json.loads(raw_payload or "{}")
		except json.JSONDecodeError:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawResponseError",
					"message": "OpenClaw gateway returned a non-JSON response.",
				},
				"runtime": "openclaw_gateway",
			}

		if not gateway_payload.get("ok"):
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawToolError",
					"message": str(gateway_payload.get("error") or "OpenClaw tool invocation failed."),
				},
				"runtime": "openclaw_gateway",
			}

		parsed_result = self._extract_gateway_result(gateway_payload.get("result"))
		if isinstance(parsed_result, dict) and parsed_result.get("error") and len(parsed_result) == 1:
			return {
				"status": "error",
				"data": {},
				"error": {
					"type": "OpenClawToolError",
					"message": str(parsed_result.get("error")),
				},
				"runtime": "openclaw_gateway",
			}
		return {
			"status": "success",
			"data": parsed_result,
			"error": None,
			"runtime": "openclaw_gateway",
		}

	def _read_gateway_token(self, config_file: str) -> str:
		if not config_file or not Path(config_file).exists():
			return ""
		try:
			config = json.loads(Path(config_file).read_text(encoding="utf-8"))
		except Exception:
			return ""
		return str(
			((config.get("gateway") or {}).get("auth") or {}).get("token")
			or ""
		)

	def _extract_gateway_result(self, result_payload: Any) -> Any:
		if not isinstance(result_payload, dict):
			return result_payload

		content = result_payload.get("content")
		if not isinstance(content, list) or not content:
			return result_payload

		text_parts = [
			str(item.get("text") or "")
			for item in content
			if isinstance(item, dict) and item.get("type") == "text"
		]
		text_payload = "\n".join(part for part in text_parts if part).strip()
		if not text_payload:
			return result_payload
		try:
			return json.loads(text_payload)
		except json.JSONDecodeError:
			return {"content": text_payload}

	def _should_use_local_fallback(self, gateway_result: dict[str, Any]) -> bool:
		error_type = str(((gateway_result or {}).get("error") or {}).get("type") or "")
		return error_type in {
			"OpenClawConfigError",
			"OpenClawTransportError",
			"OpenClawTimeoutError",
		}
