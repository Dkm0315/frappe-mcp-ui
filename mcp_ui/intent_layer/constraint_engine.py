"""Deterministic safety and permission gatekeeper."""

from __future__ import annotations

from typing import Any

import frappe


class ConstraintEngine:
	"""Validate permissions, workflows, fields, and unsafe execution."""

	SENSITIVE_TOOLS = {"delete_doc"}

	def validate_step(self, step: dict[str, Any], user_id: str) -> dict[str, Any]:
		tool = str(step.get("tool") or "")
		payload = dict(step.get("input") or {})
		doctype = str(step.get("target") or payload.get("doctype") or "")
		violations: list[str] = []
		suggestions: list[str] = []

		if tool in self.SENSITIVE_TOOLS and not payload.get("confirm"):
			violations.append("Unsafe delete blocked: confirm=true is required.")
			suggestions.append("Ask the user for explicit delete confirmation.")

		if doctype:
			if not frappe.db.exists("DocType", doctype):
				return {
					"allowed": False,
					"violations": [f"Unknown DocType: {doctype}"],
					"suggestions": ["Refresh schema or clarify the target document type."],
				}
			perm_violation = self._validate_permission(tool, doctype, payload, user_id)
			if perm_violation:
				violations.append(perm_violation)
			violations.extend(self._validate_fields(tool, doctype, payload))
			violations.extend(self._validate_workflow(tool, doctype, payload, user_id))
			violations.extend(self._validate_links(tool, doctype, payload))

		return {
			"allowed": not violations,
			"violations": violations,
			"suggestions": suggestions,
		}

	def validate_plan(self, steps: list[dict[str, Any]], user_id: str) -> dict[str, Any]:
		all_violations = []
		all_suggestions = []
		for step in steps:
			result = self.validate_step(step, user_id)
			if not result.get("allowed"):
				all_violations.extend(
					[
						f"{step.get('step_id') or step.get('action')}: {violation}"
						for violation in result.get("violations") or []
					]
				)
				all_suggestions.extend(result.get("suggestions") or [])
		return {
			"allowed": not all_violations,
			"violations": all_violations,
			"suggestions": sorted(set(all_suggestions)),
		}

	def _validate_permission(
		self,
		tool: str,
		doctype: str,
		payload: dict[str, Any],
		user_id: str,
	) -> str:
		ptype = "read"
		if tool == "create_doc":
			ptype = "create"
		elif tool in {"update_doc", "apply_workflow", "call_custom_api"}:
			ptype = "write"
		elif tool == "delete_doc":
			ptype = "delete"
		elif tool == "submit_doc":
			ptype = "submit"
		doc_name = payload.get("name")
		if not frappe.has_permission(doctype, ptype=ptype, doc=doc_name, user=user_id):
			return f"Permission denied: {user_id} lacks {ptype} on {doctype}"
		return ""

	def _validate_fields(self, tool: str, doctype: str, payload: dict[str, Any]) -> list[str]:
		if tool not in {"create_doc", "update_doc", "validate_doc"}:
			return []
		meta = frappe.get_meta(doctype)
		data = dict(payload.get("data") or {})
		if tool == "validate_doc" and not data:
			data = dict(payload)
			data.pop("doctype", None)
			data.pop("user_id", None)
		violations: list[str] = []
		valid_fields = {field.fieldname: field for field in meta.fields}
		for fieldname, value in data.items():
			if fieldname in {"doctype", "name"}:
				continue
			if fieldname not in valid_fields:
				violations.append(f"Unknown field for {doctype}: {fieldname}")
				continue
			field = valid_fields[fieldname]
			if field.fieldtype == "Check" and value not in {0, 1, True, False, "0", "1"}:
				violations.append(f"{fieldname} must be boolean-compatible")
		if tool == "create_doc":
			for field in meta.fields:
				if field.reqd and field.fieldtype not in {"Section Break", "Column Break", "Tab Break"}:
					if data.get(field.fieldname) in (None, "", []):
						violations.append(f"Missing required field: {field.fieldname}")
		return violations

	def _validate_workflow(
		self,
		tool: str,
		doctype: str,
		payload: dict[str, Any],
		user_id: str,
	) -> list[str]:
		workflow_name = frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1}, "name")
		if not workflow_name:
			return []
		if tool not in {"submit_doc", "apply_workflow"}:
			return []
		if not payload.get("name"):
			return ["Workflow transition requires a document name"]

		doc = frappe.get_doc(doctype, payload.get("name"))
		workflow = frappe.get_doc("Workflow", workflow_name)
		current_state = doc.get(workflow.workflow_state_field or "workflow_state") or ""
		user_roles = set(frappe.get_roles(user_id))

		if tool == "apply_workflow":
			action = payload.get("action")
			for transition in workflow.transitions:
				if transition.state == current_state and transition.action == action and transition.allowed in user_roles:
					return []
			return [
				f"Invalid workflow transition '{action}' from '{current_state}' for {doctype} {doc.name}"
			]

		if tool == "submit_doc":
			if not workflow.states:
				return []
			if doc.docstatus == 1:
				return []
			for transition in workflow.transitions:
				if transition.state == current_state and transition.allowed in user_roles:
					if any(
						state.state == transition.next_state and int(state.doc_status or 0) == 1
						for state in workflow.states
					):
						return []
			return [
				f"Submit blocked by workflow for {doctype} {doc.name}; apply a valid workflow action first"
			]
		return []

	def _validate_links(self, tool: str, doctype: str, payload: dict[str, Any]) -> list[str]:
		if tool not in {"create_doc", "update_doc", "validate_doc"}:
			return []
		meta = frappe.get_meta(doctype)
		data = dict(payload.get("data") or {})
		violations: list[str] = []
		for field in meta.fields:
			if field.fieldtype != "Link" or not field.options:
				continue
			value = data.get(field.fieldname)
			if value and not frappe.db.exists(field.options, value):
				violations.append(f"Missing linked {field.options}: {value}")
		return violations
