"""
Core MCP Tools for Frappe CRUD operations
These tools provide basic database operations with credit tracking
"""
import json

import frappe
from frappe_mcp import ToolAnnotations

from mcp_ui.api.credits import calculate_tool_cost, deduct_credits
from mcp_ui.mcp_server.mcp import mcp


def track_credits(tool_name: str, params: dict):
	"""Wrapper to track credit usage for tool execution"""
	cost = calculate_tool_cost(tool_name, params)
	deduct_credits(cost, tool_name, params)
	return cost


@mcp.tool(
	annotations=ToolAnnotations(
		title="Create Document",
		destructiveHint=False,
		idempotentHint=False,
	)
)
def create_document(doctype: str, data: dict) -> dict:
	"""
	Create a new document in Frappe.

	Args:
		doctype: The DocType name (e.g., "Customer", "Sales Order")
		data: Document field values as key-value pairs

	Returns:
		Created document with name and all fields
	"""
	# Track credits
	track_credits("create_document", {"doctype": doctype, "data": data})

	# Create document
	doc = frappe.get_doc({"doctype": doctype, **data})
	doc.insert()
	frappe.db.commit()

	return {"success": True, "name": doc.name, "doc": doc.as_dict()}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Update Document",
		destructiveHint=False,
		idempotentHint=True,
	)
)
def update_document(doctype: str, name: str, data: dict) -> dict:
	"""
	Update an existing document in Frappe.

	Args:
		doctype: The DocType name
		name: The document name/ID
		data: Fields to update as key-value pairs

	Returns:
		Updated document
	"""
	track_credits("update_document", {"doctype": doctype, "name": name})

	doc = frappe.get_doc(doctype, name)
	doc.update(data)
	doc.save()
	frappe.db.commit()

	return {"success": True, "name": doc.name, "doc": doc.as_dict()}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Delete Document",
		destructiveHint=True,
		idempotentHint=False,
	)
)
def delete_document(doctype: str, name: str) -> dict:
	"""
	Delete a document from Frappe.

	Args:
		doctype: The DocType name
		name: The document name/ID

	Returns:
		Success confirmation
	"""
	track_credits("delete_document", {"doctype": doctype, "name": name})

	frappe.delete_doc(doctype, name)
	frappe.db.commit()

	return {"success": True, "message": f"Deleted {doctype} {name}"}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Get Document",
		readOnlyHint=True,
		idempotentHint=True,
	)
)
def get_document(doctype: str, name: str) -> dict:
	"""
	Fetch a single document from Frappe.

	Args:
		doctype: The DocType name
		name: The document name/ID

	Returns:
		Document data
	"""
	track_credits("get_document", {"doctype": doctype, "name": name})

	doc = frappe.get_doc(doctype, name)
	return {"success": True, "doc": doc.as_dict()}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Get List",
		readOnlyHint=True,
		idempotentHint=True,
	)
)
def get_list(doctype: str, filters: dict = None, fields: list = None, limit: int = 20) -> dict:
	"""
	Get a list of documents with optional filters.

	Args:
		doctype: The DocType name
		filters: Filter conditions as key-value pairs
		fields: List of fields to fetch
		limit: Maximum number of records to return

	Returns:
		List of documents
	"""
	track_credits("get_list", {"doctype": doctype, "limit": limit})

	docs = frappe.get_all(
		doctype, filters=filters or {}, fields=fields or ["name"], limit=limit, order_by="modified desc"
	)

	return {"success": True, "count": len(docs), "docs": docs}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Search Documents",
		readOnlyHint=True,
		idempotentHint=True,
	)
)
def search_documents(doctype: str, search_text: str, limit: int = 20) -> dict:
	"""
	Search documents by text across searchable fields.

	Args:
		doctype: The DocType name
		search_text: Text to search for
		limit: Maximum number of results

	Returns:
		List of matching documents
	"""
	track_credits("search_documents", {"doctype": doctype, "limit": limit})

	# Get searchable fields for the doctype
	meta = frappe.get_meta(doctype)
	search_fields = [df.fieldname for df in meta.fields if df.fieldtype in ["Data", "Text", "Small Text"]]

	if not search_fields:
		search_fields = ["name"]

	# Build search filters
	filters = []
	for field in search_fields[:3]:  # Limit to 3 fields for performance
		filters.append([doctype, field, "like", f"%{search_text}%"])

	docs = frappe.get_all(doctype, or_filters=filters, fields=["name", *search_fields[:3]], limit=limit)

	return {"success": True, "count": len(docs), "docs": docs}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Execute Report",
		readOnlyHint=True,
		idempotentHint=True,
	)
)
def execute_report(report_name: str, filters: dict = None) -> dict:
	"""
	Execute a Frappe report and get results.

	Args:
		report_name: Name of the report to execute
		filters: Report filters as key-value pairs

	Returns:
		Report results
	"""
	track_credits("execute_report", {"report_name": report_name})

	report = frappe.get_doc("Report", report_name)
	filters = filters or {}

	from frappe.desk.query_report import run as run_query_report

	result = run_query_report(report_name, filters)

	return {"success": True, "columns": result.get("columns", []), "data": result.get("result", [])}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Bulk Update",
		destructiveHint=False,
		idempotentHint=False,
	)
)
def bulk_update(doctype: str, filters: dict, update_data: dict) -> dict:
	"""
	Update multiple documents matching filters.

	Args:
		doctype: The DocType name
		filters: Filter conditions to select documents
		update_data: Fields to update on all matched documents

	Returns:
		Count of updated documents
	"""
	track_credits("bulk_update", {"doctype": doctype, "filters": filters})

	docs = frappe.get_all(doctype, filters=filters, pluck="name")

	updated_count = 0
	for name in docs:
		doc = frappe.get_doc(doctype, name)
		doc.update(update_data)
		doc.save()
		updated_count += 1

	frappe.db.commit()

	return {"success": True, "updated_count": updated_count, "documents": docs}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Export Data",
		readOnlyHint=True,
		idempotentHint=True,
	)
)
def export_data(doctype: str, filters: dict = None, fields: list = None, limit: int = 100) -> dict:
	"""
	Export data in JSON format.

	Args:
		doctype: The DocType name
		filters: Filter conditions
		fields: Fields to export
		limit: Maximum records to export

	Returns:
		Exported data
	"""
	track_credits("export_data", {"doctype": doctype, "limit": limit})

	docs = frappe.get_all(doctype, filters=filters or {}, fields=fields or ["*"], limit=limit)

	return {
		"success": True,
		"doctype": doctype,
		"count": len(docs),
		"data": docs,
		"format": "json",
	}


@mcp.tool(
	annotations=ToolAnnotations(
		title="Get Dashboard Data",
		readOnlyHint=True,
		idempotentHint=True,
	)
)
def get_dashboard_data(doctype: str) -> dict:
	"""
	Get dashboard statistics for a DocType.

	Args:
		doctype: The DocType name

	Returns:
		Dashboard metrics and statistics
	"""
	track_credits("get_dashboard_data", {"doctype": doctype})

	# Get total count
	total = frappe.db.count(doctype)

	# Get recent records
	recent = frappe.get_all(doctype, fields=["name", "modified"], order_by="modified desc", limit=5)

	# Try to get status-wise count if status field exists
	status_count = {}
	meta = frappe.get_meta(doctype)
	if meta.has_field("status"):
		statuses = frappe.get_all(doctype, fields=["status"], group_by="status")
		for status_doc in statuses:
			status = status_doc.get("status")
			count = frappe.db.count(doctype, {"status": status})
			status_count[status] = count

	return {
		"success": True,
		"doctype": doctype,
		"total_count": total,
		"status_breakdown": status_count,
		"recent_records": recent,
	}
