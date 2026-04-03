"""Structured logging helpers backed by MCP Usage Log and bench logs."""

from __future__ import annotations

import json
from typing import Any

import frappe


def log_stage(
	request_id: str,
	stage: str,
	status: str = "Success",
	input_payload: dict[str, Any] | None = None,
	output_payload: dict[str, Any] | None = None,
	error_message: str = "",
	retry_count: int = 0,
	error_type: str = "",
) -> None:
	"""Persist stage traces in the existing MCP Usage Log DocType."""
	try:
		frappe.get_doc(
			{
				"doctype": "MCP Usage Log",
				"user": frappe.session.user,
				"tool_name": stage,
				"credits_consumed": 0,
				"status": status,
				"request_id": request_id,
				"stage_name": stage,
				"retry_count": retry_count,
				"error_type": error_type,
				"input_params": json.dumps(input_payload or {}, default=str)[:10000],
				"output": json.dumps(output_payload or {}, default=str)[:10000],
				"error_message": (error_message or "")[:1400],
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass

	try:
		logger = frappe.logger("intent_layer")
		if status == "Failed":
			logger.error(f"{request_id} [{stage}] {error_message}")
		else:
			logger.info(f"{request_id} [{stage}] {status}")
	except Exception:
		pass
