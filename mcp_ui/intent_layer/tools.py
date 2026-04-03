"""Deterministic tool contract executed after planner + constraints."""

from __future__ import annotations

import inspect
from typing import Any, Callable

import frappe
from frappe.model.workflow import apply_workflow as frappe_apply_workflow


class ToolExecutionError(Exception):
	"""Raised when a deterministic tool invocation fails."""


def _set_user(user_id: str | None = None) -> None:
	if user_id:
		frappe.set_user(user_id)


def _check_permission(doctype: str, ptype: str, name: str | None = None) -> None:
	if not frappe.has_permission(doctype, ptype=ptype, doc=name):
		raise frappe.PermissionError(f"You don't have {ptype} permission for {doctype}")


def create_doc(doctype: str, data: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "create")
	doc = frappe.get_doc({"doctype": doctype, **(data or {})})
	doc.insert()
	frappe.db.commit()
	return {"doctype": doctype, "name": doc.name, "doc": doc.as_dict()}


def get_doc(doctype: str, name: str, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "read", name)
	doc = frappe.get_doc(doctype, name)
	return {"doctype": doctype, "name": doc.name, "doc": doc.as_dict()}


def update_doc(doctype: str, name: str, data: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "write", name)
	doc = frappe.get_doc(doctype, name)
	doc.update(data or {})
	doc.save()
	frappe.db.commit()
	return {"doctype": doctype, "name": doc.name, "doc": doc.as_dict()}


def delete_doc(doctype: str, name: str, confirm: bool = False, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	if not confirm:
		raise ToolExecutionError("Delete requires confirm=true and is blocked by default.")
	_check_permission(doctype, "delete", name)
	frappe.delete_doc(doctype, name)
	frappe.db.commit()
	return {"doctype": doctype, "name": name, "deleted": True}


def search_docs(
	doctype: str,
	filters: dict[str, Any] | None = None,
	query: str = "",
	limit: int = 20,
	user_id: str | None = None,
) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "read")
	meta = frappe.get_meta(doctype)
	search_fields = [
		field.fieldname
		for field in meta.fields
		if field.fieldtype in {"Data", "Text", "Small Text", "Long Text"}
	][:4]
	if not search_fields:
		search_fields = ["name"]
	or_filters = [[doctype, field, "like", f"%{query}%"] for field in search_fields] if query else None
	docs = frappe.get_all(
		doctype,
		filters=filters or {},
		or_filters=or_filters,
		fields=["name", *[field for field in search_fields if field != "name"]],
		limit=min(limit or 20, 200),
		order_by="modified desc",
	)
	return {"doctype": doctype, "count": len(docs), "docs": docs}


def list_docs(
	doctype: str,
	filters: dict[str, Any] | None = None,
	fields: list[str] | None = None,
	limit: int = 20,
	user_id: str | None = None,
) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "read")
	docs = frappe.get_all(
		doctype,
		filters=filters or {},
		fields=fields or ["name"],
		limit=min(limit or 20, 200),
		order_by="modified desc",
	)
	return {"doctype": doctype, "count": len(docs), "docs": docs}


def get_schema(doctype: str, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "read")
	meta = frappe.get_meta(doctype)
	return {
		"doctype": doctype,
		"module": meta.module,
		"is_submittable": bool(meta.is_submittable),
		"fields": [
			{
				"fieldname": field.fieldname,
				"label": field.label,
				"fieldtype": field.fieldtype,
				"required": bool(field.reqd),
				"options": field.options,
			}
			for field in meta.fields
			if field.fieldtype not in {"Section Break", "Column Break", "Tab Break"}
		],
	}


def list_doctypes(limit: int = 500, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	doctypes = frappe.get_all(
		"DocType",
		filters={"istable": 0},
		fields=["name", "module", "custom"],
		order_by="name asc",
		limit=min(limit or 500, 2000),
	)
	allowed = [
		dt
		for dt in doctypes
		if frappe.has_permission(dt["name"], ptype="read")
	]
	return {"count": len(allowed), "doctypes": allowed}


def validate_doc(doctype: str, data: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	meta = frappe.get_meta(doctype)
	violations: list[str] = []
	payload = data or {}
	for field in meta.fields:
		if field.fieldtype in {"Section Break", "Column Break", "Tab Break"}:
			continue
		if field.reqd and payload.get(field.fieldname) in (None, "", []):
			violations.append(f"{field.fieldname} is mandatory")
		if field.fieldtype == "Link" and payload.get(field.fieldname) and field.options:
			if not frappe.db.exists(field.options, payload.get(field.fieldname)):
				violations.append(
					f"{field.fieldname} references missing {field.options}: {payload.get(field.fieldname)}"
				)
	return {"allowed": not violations, "violations": violations}


def submit_doc(doctype: str, name: str, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "submit", name)
	doc = frappe.get_doc(doctype, name)
	doc.submit()
	frappe.db.commit()
	return {"doctype": doctype, "name": doc.name, "docstatus": doc.docstatus, "doc": doc.as_dict()}


def apply_workflow(
	doctype: str,
	name: str,
	action: str,
	user_id: str | None = None,
) -> dict[str, Any]:
	_set_user(user_id)
	_check_permission(doctype, "write", name)
	doc = frappe.get_doc(doctype, name)
	updated = frappe_apply_workflow(doc, action)
	frappe.db.commit()
	return {
		"doctype": doctype,
		"name": updated.name,
		"workflow_state": updated.get("workflow_state"),
		"docstatus": updated.docstatus,
		"doc": updated.as_dict(),
	}


def get_recent_docs(doctype: str = "", limit: int = 5, user_id: str | None = None) -> dict[str, Any]:
	_set_user(user_id)
	filters = {"istable": 0}
	if doctype:
		_check_permission(doctype, "read")
		return {
			"doctype": doctype,
			"docs": frappe.get_all(
				doctype,
				fields=["name", "modified"],
				order_by="modified desc",
				limit=min(limit or 5, 50),
			),
		}
	doctypes = frappe.get_all("DocType", filters=filters, pluck="name", limit=200)
	recent = []
	for dt in doctypes:
		if not frappe.has_permission(dt, ptype="read"):
			continue
		try:
			rows = frappe.get_all(dt, fields=["name", "modified"], order_by="modified desc", limit=1)
		except Exception:
			continue
		for row in rows:
			recent.append({"doctype": dt, "name": row.name, "modified": row.modified})
	recent.sort(key=lambda row: str(row.get("modified") or ""), reverse=True)
	return {"docs": recent[: min(limit or 5, 50)]}


def call_custom_api(
	method: str,
	params: dict[str, Any] | None = None,
	user_id: str | None = None,
) -> dict[str, Any]:
	_set_user(user_id)
	fn = frappe.get_attr(method)
	frappe.is_whitelisted(fn)
	filtered_params = _filter_method_params(fn, params or {})
	output = fn(**filtered_params)
	frappe.db.commit()
	return {"method": method, "params": filtered_params, "result": output}


TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
	"create_doc": create_doc,
	"get_doc": get_doc,
	"update_doc": update_doc,
	"delete_doc": delete_doc,
	"search_docs": search_docs,
	"list_docs": list_docs,
	"get_schema": get_schema,
	"list_doctypes": list_doctypes,
	"validate_doc": validate_doc,
	"submit_doc": submit_doc,
	"apply_workflow": apply_workflow,
	"get_recent_docs": get_recent_docs,
	"call_custom_api": call_custom_api,
}


def execute_tool_call(tool: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
	fn = TOOL_REGISTRY.get(tool)
	if not fn:
		raise ToolExecutionError(f"Unknown tool: {tool}")
	return fn(**(params or {}))


def _filter_method_params(fn: Callable[..., Any], params: dict[str, Any]) -> dict[str, Any]:
	try:
		signature = inspect.signature(fn)
	except (TypeError, ValueError):
		return dict(params or {})

	parameters = signature.parameters
	if any(
		param.kind == inspect.Parameter.VAR_KEYWORD
		for param in parameters.values()
	):
		return dict(params or {})

	accepted_names = {
		name
		for name, param in parameters.items()
		if param.kind in {
			inspect.Parameter.POSITIONAL_OR_KEYWORD,
			inspect.Parameter.KEYWORD_ONLY,
		}
		and name not in {"self", "cls"}
	}
	return {
		key: value
		for key, value in (params or {}).items()
		if key in accepted_names
	}


def get_tool_schema() -> dict[str, dict[str, Any]]:
	return {
		"create_doc": {"required": ["doctype", "data"]},
		"get_doc": {"required": ["doctype", "name"]},
		"update_doc": {"required": ["doctype", "name", "data"]},
		"delete_doc": {"required": ["doctype", "name", "confirm"]},
		"search_docs": {"required": ["doctype"]},
		"list_docs": {"required": ["doctype"]},
		"get_schema": {"required": ["doctype"]},
		"list_doctypes": {"required": []},
		"validate_doc": {"required": ["doctype", "data"]},
		"submit_doc": {"required": ["doctype", "name"]},
		"apply_workflow": {"required": ["doctype", "name", "action"]},
		"get_recent_docs": {"required": []},
		"call_custom_api": {"required": ["method"]},
	}
