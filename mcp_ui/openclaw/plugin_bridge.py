from __future__ import annotations

import json
import os
import sys
from typing import Any


def _emit(payload: dict[str, Any], exit_code: int = 0) -> None:
	sys.stdout.write(json.dumps(payload, default=str))
	sys.stdout.write("\n")
	sys.exit(exit_code)


def _read_payload() -> dict[str, Any]:
	try:
		raw = sys.stdin.read().strip()
		if not raw:
			return {}
		return json.loads(raw)
	except Exception as exc:
		_emit({"success": False, "error": f"Invalid JSON payload: {exc}"}, exit_code=1)
		return {}


def _init_frappe():
	bench_path = os.environ.get("FRAPPE_BENCH") or os.getcwd()
	site = os.environ.get("FRAPPE_SITE", "site1.local")
	sites_path = os.path.join(bench_path, "sites") if bench_path else None

	if bench_path and os.path.isdir(bench_path):
		sys.path.insert(0, os.path.join(bench_path, "apps", "frappe"))
		if sites_path and os.path.isdir(sites_path):
			os.chdir(sites_path)
		else:
			os.chdir(bench_path)

	import frappe

	frappe.init(site=site, sites_path=sites_path)
	frappe.connect()
	frappe.set_user(os.environ.get("FRAPPE_BOOT_USER", "Administrator"))
	return frappe


def _handle(operation: str, payload: dict[str, Any]) -> Any:
	from mcp_ui.openclaw.federation import (
		execute_as_mapped_user,
		get_action_catalog_payload,
		get_session_mode_payload,
		plan_request_with_context_payload,
		prepare_create_record_payload,
		retrieve_site_context_payload,
		resolve_identity_record,
		set_session_mode_payload,
	)
	from mcp_ui.openclaw.site_context import (
		get_change_summary,
		get_site_manifest,
		search_site_context,
		refresh_site_context,
	)

	if operation == "ping":
		return {"success": True, "site": payload.get("site")}
	if operation == "resolve_identity":
		return resolve_identity_record(
			channel=payload.get("channel", ""),
			external_id=payload.get("external_id"),
			external_username=payload.get("external_username"),
			site_hint=payload.get("site"),
			chat_id=payload.get("chat_id"),
			thread_id=payload.get("thread_id"),
		)
	if operation == "get_site_manifest":
		return get_site_manifest(
			site=payload.get("site"),
			refresh=bool(payload.get("refresh")),
			detail_level=payload.get("detail_level", "summary"),
			sections=payload.get("sections"),
			limit_per_section=int(payload.get("limit_per_section") or 10),
		)
	if operation == "search_site_context":
		return search_site_context(
			site=payload.get("site"),
			query=payload.get("query", ""),
			sections=payload.get("sections"),
			limit=int(payload.get("limit") or 12),
		)
	if operation == "refresh_site_context":
		return refresh_site_context(site=payload.get("site"), reason=payload.get("reason", "plugin"))
	if operation == "get_change_summary":
		return get_change_summary(
			site=payload.get("site"),
			since_hash_or_timestamp=payload.get("since_hash_or_timestamp"),
		)
	if operation == "get_action_catalog":
		return get_action_catalog_payload(
			query=payload.get("query", ""),
			category=payload.get("category", ""),
			write_only=bool(payload.get("write_only")),
			destructive_only=bool(payload.get("destructive_only")),
			limit=int(payload.get("limit") or 12),
			verbose=bool(payload.get("verbose")),
		)
	if operation == "get_session_mode":
		return get_session_mode_payload(payload.get("session_context") or {})
	if operation == "set_session_mode":
		return set_session_mode_payload(
			payload.get("session_context") or {},
			mode=payload.get("mode", "normal"),
		)
	if operation == "retrieve_site_context":
		return retrieve_site_context_payload(
			site=payload.get("site"),
			query=payload.get("query", ""),
			limit=int(payload.get("limit") or 5),
		)
	if operation == "plan_request":
		return plan_request_with_context_payload(
			session_context=payload.get("session_context") or {},
			request=payload.get("request", ""),
			draft=payload.get("draft") or {},
		)
	if operation == "execute_as_user":
		return execute_as_mapped_user(
			session_context=payload.get("session_context") or {},
			action=payload.get("action", ""),
			args=payload.get("args") or {},
			validate_only=bool(payload.get("validate_only")),
			confirmed=bool(payload.get("confirmed")),
			confirmation_note=payload.get("confirmation_note", ""),
		)
	if operation == "prepare_create_record":
		return prepare_create_record_payload(
			session_context=payload.get("session_context") or {},
			request=payload.get("request", ""),
			doctype=payload.get("doctype", ""),
			draft=payload.get("draft") or {},
		)

	raise ValueError(f"Unsupported bridge operation: {operation}")


def main() -> None:
	if len(sys.argv) < 2:
		_emit({"success": False, "error": "Missing bridge operation"}, exit_code=1)

	operation = sys.argv[1]
	payload = _read_payload()
	frappe = _init_frappe()

	try:
		result = _handle(operation, payload)
		_emit(result if isinstance(result, dict) else {"success": True, "result": result})
	except Exception as exc:
		_emit({"success": False, "error": str(exc), "operation": operation}, exit_code=1)
	finally:
		try:
			frappe.destroy()
		except Exception:
			pass


if __name__ == "__main__":
	main()
