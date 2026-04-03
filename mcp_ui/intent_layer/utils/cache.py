"""Site-aware cache helpers."""

from __future__ import annotations

import json
from typing import Any

import frappe


def _prefix(key: str) -> str:
	site = getattr(frappe.local, "site", None) or "default"
	return f"mcp_ui:intent_layer:{site}:{key}"


def cache_get(key: str) -> Any:
	try:
		value = frappe.cache().get_value(_prefix(key))
	except Exception:
		return None
	if isinstance(value, (bytes, bytearray)):
		value = value.decode("utf-8")
	if isinstance(value, str):
		try:
			return json.loads(value)
		except Exception:
			return value
	return value


def cache_set(key: str, value: Any, expires_in_sec: int = 3600) -> None:
	try:
		frappe.cache().set_value(_prefix(key), json.dumps(value, default=str), expires_in_sec=expires_in_sec)
	except Exception:
		return


def cache_delete(key: str) -> None:
	try:
		frappe.cache().delete_value(_prefix(key))
	except Exception:
		return
