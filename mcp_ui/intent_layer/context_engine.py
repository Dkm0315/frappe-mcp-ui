"""Runtime context resolution layer."""

from __future__ import annotations

import json
from typing import Any

import frappe

from mcp_ui.intent_layer.models.context import ContextResolution
from mcp_ui.intent_layer.models.intent import IntentPayload
from mcp_ui.intent_layer.utils.cache import cache_get, cache_set


class ContextEngine:
	"""Resolve follow-up references using recent docs, logs, and user role context."""

	MEMORY_KEY_PREFIX = "session_memory"

	def resolve(self, intent_payload: dict[str, Any], user_id: str) -> ContextResolution:
		intent = IntentPayload.from_dict(intent_payload)
		recent_docs = self._load_recent_docs(user_id)
		memory = cache_get(self._memory_key(user_id)) or {}
		resolved_target = intent.target_candidates[0] if intent.target_candidates else ""
		resolved_doc = ""
		resolved_entities = dict(intent.entities or {})
		confidence = intent.confidence

		if resolved_entities.get("context_reference") and recent_docs:
			best_doc = self._choose_recent_doc(recent_docs, resolved_target)
			if best_doc and frappe.db.exists(best_doc.get("doctype"), best_doc.get("name")):
				resolved_target = best_doc.get("doctype") or resolved_target
				resolved_doc = best_doc.get("name") or ""
				resolved_entities.setdefault("name", resolved_doc)
				confidence = max(confidence, 0.9)

		if not resolved_doc and memory.get("last_doc"):
			last_doc = memory.get("last_doc") or {}
			if (
				last_doc.get("doctype")
				and last_doc.get("name")
				and frappe.db.exists(last_doc.get("doctype"), last_doc.get("name"))
				and (not resolved_target or last_doc.get("doctype") == resolved_target)
			):
				resolved_target = last_doc.get("doctype") or resolved_target
				resolved_doc = last_doc.get("name") or ""
				if resolved_doc:
					confidence = max(confidence, 0.85)
			elif last_doc.get("doctype") and last_doc.get("name") and not frappe.db.exists(
				last_doc.get("doctype"),
				last_doc.get("name"),
			):
				memory.pop("last_doc", None)

		if resolved_target:
			resolved_entities.setdefault("doctype", resolved_target)
		if resolved_doc:
			resolved_entities.setdefault("document_name", resolved_doc)

		context = ContextResolution(
			user_id=user_id,
			intent=intent,
			resolved_target=resolved_target,
			resolved_doc=resolved_doc,
			resolved_entities=resolved_entities,
			recent_docs=recent_docs,
			context_confidence=round(min(confidence or 0.0, 0.99), 4),
		)
		cache_set(
			self._memory_key(user_id),
			{
				"last_intent": intent.to_dict(),
				"last_context": context.to_dict(),
				"last_doc": {"doctype": resolved_target, "name": resolved_doc} if resolved_doc else memory.get("last_doc"),
			},
			expires_in_sec=86400,
		)
		return context

	def remember_document(self, user_id: str, doctype: str, name: str) -> None:
		if not doctype or not name:
			return
		memory = cache_get(self._memory_key(user_id)) or {}
		memory["last_doc"] = {"doctype": doctype, "name": name}
		cache_set(self._memory_key(user_id), memory, expires_in_sec=86400)

	def _load_recent_docs(self, user_id: str) -> list[dict[str, Any]]:
		docs: list[dict[str, Any]] = []
		try:
			logs = frappe.get_all(
				"MCP Usage Log",
				filters={"user": user_id, "status": ["in", ["Success", "Partial"]]},
				fields=["tool_name", "output", "modified"],
				order_by="modified desc",
				limit=30,
			)
		except Exception:
			logs = []

		for row in logs:
			try:
				output = json.loads(row.output or "{}")
			except Exception:
				continue
			doctype = output.get("doctype") or (output.get("doc") or {}).get("doctype")
			name = output.get("name") or (output.get("doc") or {}).get("name")
			if doctype and name and frappe.db.exists(doctype, name):
				docs.append({"doctype": doctype, "name": name, "modified": row.modified})
			if output.get("docs") and isinstance(output.get("docs"), list):
				for item in output.get("docs") or []:
					item_doctype = output.get("doctype") or item.get("doctype") or ""
					item_name = item.get("name")
					if item_doctype and item_name and frappe.db.exists(item_doctype, item_name):
						docs.append(
							{
								"doctype": item_doctype,
								"name": item_name,
								"modified": item.get("modified") or row.modified,
							}
						)
		seen = set()
		unique_docs = []
		for row in docs:
			key = (row.get("doctype"), row.get("name"))
			if key in seen or not key[0] or not key[1]:
				continue
			seen.add(key)
			unique_docs.append(row)
		return unique_docs[:10]

	def _choose_recent_doc(self, recent_docs: list[dict[str, Any]], resolved_target: str) -> dict[str, Any] | None:
		if resolved_target:
			for row in recent_docs:
				if row.get("doctype") == resolved_target:
					return row
		return recent_docs[0] if recent_docs else None

	def _memory_key(self, user_id: str) -> str:
		return f"{self.MEMORY_KEY_PREFIX}:{user_id or frappe.session.user}"
