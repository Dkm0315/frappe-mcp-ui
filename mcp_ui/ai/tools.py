"""
AI Tool Definitions for Frappe Business Automation
26 tools covering: CRUD, Document Lifecycle, Bulk Ops, Excel, Reports, Process Intelligence, Automation

Each tool returns a dict result. The AI engine calls these as the logged-in user,
so Frappe's permission system automatically enforces RBAC.
"""
import json

import frappe

from mcp_ui.ai.providers import check_ai_access

# ──────────────────────────────────────────────
# Tool Registry
# ──────────────────────────────────────────────

TOOLS = []


def _register(schema: dict):
	"""Decorator to register a tool function with its schema."""

	def decorator(fn):
		fn._schema = schema
		TOOLS.append({"function": fn, "schema": schema})
		return fn

	return decorator


def get_tool_schemas() -> list:
	"""Return all tool schemas in litellm/OpenAI function-calling format."""
	return [
		{
			"type": "function",
			"function": t["schema"],
		}
		for t in TOOLS
	]


def get_tool_map() -> dict:
	"""Return a map of tool_name -> callable."""
	return {t["schema"]["name"]: t["function"] for t in TOOLS}


def _check_access(doctype: str, operation: str = "read"):
	"""Check AI access control. Raises if denied."""
	if not check_ai_access(doctype, operation):
		raise PermissionError(f"AI access to {doctype} ({operation}) is not enabled by the administrator.")


def _check_permission(doctype: str, ptype: str = "read", doc: str = None):
	"""Check Frappe user permission. Raises if denied."""
	if not frappe.has_permission(doctype, ptype=ptype, doc=doc):
		raise frappe.PermissionError(f"You don't have {ptype} permission for {doctype}")


# ──────────────────────────────────────────────
# 1-6: Core CRUD
# ──────────────────────────────────────────────

@_register({
	"name": "get_list",
	"description": "Get a list of documents with filters, field selection, ordering, and pagination. Use this for queries like 'show me all open Sales Orders' or 'list customers from Mumbai'.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name (e.g. 'Sales Order', 'Customer')"},
			"filters": {"type": "object", "description": "Filter conditions as key-value pairs. Use operators like ['>', 10], ['like', '%test%'], ['in', ['Draft', 'Open']]"},
			"fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to return. Default: ['name']. Use ['*'] for all fields."},
			"order_by": {"type": "string", "description": "Sort order, e.g. 'modified desc', 'creation asc'"},
			"limit": {"type": "integer", "description": "Max records to return (default 20, max 500)"},
			"start": {"type": "integer", "description": "Offset for pagination (default 0)"},
		},
		"required": ["doctype"],
	},
})
def get_list(doctype: str, filters: dict = None, fields: list = None, order_by: str = None, limit: int = 20, start: int = 0) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read")

	limit = min(limit or 20, 500)
	docs = frappe.get_list(
		doctype,
		filters=filters or {},
		fields=fields or ["name"],
		order_by=order_by or "modified desc",
		limit_page_length=limit,
		limit_start=start or 0,
	)
	return {"success": True, "doctype": doctype, "count": len(docs), "data": docs}


@_register({
	"name": "get_document",
	"description": "Fetch a single document with all its fields. Use this to inspect a specific record like 'show me Sales Order SO-00145'.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The document name/ID"},
		},
		"required": ["doctype", "name"],
	},
})
def get_document(doctype: str, name: str) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read", name)

	doc = frappe.get_doc(doctype, name)
	return {"success": True, "doctype": doctype, "name": doc.name, "data": doc.as_dict()}


@_register({
	"name": "create_document",
	"description": "Create a new document. Use this for simple standalone docs (ToDo, Note, etc). For downstream docs (DN from SO, SI from DN), use make_mapped_document instead.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"data": {"type": "object", "description": "Document field values as key-value pairs"},
		},
		"required": ["doctype", "data"],
	},
})
def create_document(doctype: str, data: dict) -> dict:
	_check_access(doctype, "create")
	_check_permission(doctype, "create")

	doc = frappe.get_doc({"doctype": doctype, **data})
	doc.insert()
	frappe.db.commit()
	return {"success": True, "doctype": doctype, "name": doc.name, "data": doc.as_dict()}


@_register({
	"name": "update_document",
	"description": "Update fields on an existing document. Provide only the fields you want to change.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The document name/ID"},
			"data": {"type": "object", "description": "Fields to update as key-value pairs"},
		},
		"required": ["doctype", "name", "data"],
	},
})
def update_document(doctype: str, name: str, data: dict) -> dict:
	_check_access(doctype, "update")
	_check_permission(doctype, "write", name)

	doc = frappe.get_doc(doctype, name)
	doc.update(data)
	doc.save()
	frappe.db.commit()
	return {"success": True, "doctype": doctype, "name": doc.name, "data": doc.as_dict()}


@_register({
	"name": "delete_document",
	"description": "Delete a document. Always confirm with the user before deleting.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The document name/ID"},
		},
		"required": ["doctype", "name"],
	},
})
def delete_document(doctype: str, name: str) -> dict:
	_check_access(doctype, "delete")
	_check_permission(doctype, "delete", name)

	frappe.delete_doc(doctype, name)
	frappe.db.commit()
	return {"success": True, "message": f"Deleted {doctype} {name}"}


@_register({
	"name": "search_documents",
	"description": "Full-text search across a DocType's searchable fields. Use for fuzzy queries like 'find customers with Mumbai in their name'.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"search_text": {"type": "string", "description": "Text to search for"},
			"limit": {"type": "integer", "description": "Max results (default 20)"},
		},
		"required": ["doctype", "search_text"],
	},
})
def search_documents(doctype: str, search_text: str, limit: int = 20) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read")

	meta = frappe.get_meta(doctype)
	search_fields = [df.fieldname for df in meta.fields if df.fieldtype in ("Data", "Text", "Small Text")][:3]
	if not search_fields:
		search_fields = ["name"]

	or_filters = [[doctype, f, "like", f"%{search_text}%"] for f in search_fields]
	docs = frappe.get_list(
		doctype,
		or_filters=or_filters,
		fields=["name", *search_fields],
		limit_page_length=min(limit, 100),
	)
	return {"success": True, "doctype": doctype, "count": len(docs), "data": docs}


# ──────────────────────────────────────────────
# 7-10: Document Lifecycle
# ──────────────────────────────────────────────

@_register({
	"name": "submit_document",
	"description": "Submit a Draft document. This triggers workflows and validations. Use after creating a Sales Order, Purchase Order, etc.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The document name/ID"},
		},
		"required": ["doctype", "name"],
	},
})
def submit_document(doctype: str, name: str) -> dict:
	_check_access(doctype, "update")
	_check_permission(doctype, "submit", name)

	doc = frappe.get_doc(doctype, name)
	doc.submit()
	frappe.db.commit()
	return {"success": True, "doctype": doctype, "name": doc.name, "docstatus": doc.docstatus, "data": doc.as_dict()}


@_register({
	"name": "cancel_document",
	"description": "Cancel a submitted document. This may require cancelling linked downstream documents first.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The document name/ID"},
		},
		"required": ["doctype", "name"],
	},
})
def cancel_document(doctype: str, name: str) -> dict:
	_check_access(doctype, "update")
	_check_permission(doctype, "cancel", name)

	doc = frappe.get_doc(doctype, name)
	doc.cancel()
	frappe.db.commit()
	return {"success": True, "doctype": doctype, "name": doc.name, "docstatus": doc.docstatus}


@_register({
	"name": "amend_document",
	"description": "Amend a cancelled document. Creates a new version with '-1' suffix. Use when a submitted doc was cancelled and needs corrections.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The cancelled document name/ID"},
		},
		"required": ["doctype", "name"],
	},
})
def amend_document(doctype: str, name: str) -> dict:
	_check_access(doctype, "create")
	_check_permission(doctype, "amend", name)

	doc = frappe.get_doc(doctype, name)
	amended = frappe.copy_doc(doc)
	amended.amended_from = name
	amended.docstatus = 0
	amended.insert()
	frappe.db.commit()
	return {"success": True, "doctype": doctype, "original": name, "amended_name": amended.name, "data": amended.as_dict()}


@_register({
	"name": "make_mapped_document",
	"description": "Create a downstream document from an upstream one with proper field mapping. This is the KEY tool for business process chains: Sales Order → Delivery Note, Delivery Note → Sales Invoice, Purchase Order → Purchase Receipt, etc. Uses Frappe's native document mapper which auto-maps items, taxes, and all linked fields.",
	"parameters": {
		"type": "object",
		"properties": {
			"source_doctype": {"type": "string", "description": "The source DocType (e.g. 'Sales Order')"},
			"source_name": {"type": "string", "description": "The source document name (e.g. 'SO-00145')"},
			"target_doctype": {"type": "string", "description": "The target DocType to create (e.g. 'Delivery Note')"},
		},
		"required": ["source_doctype", "source_name", "target_doctype"],
	},
})
def make_mapped_document(source_doctype: str, source_name: str, target_doctype: str) -> dict:
	_check_access(source_doctype, "read")
	_check_access(target_doctype, "create")
	_check_permission(source_doctype, "read", source_name)
	_check_permission(target_doctype, "create")

	# Use Frappe's standard mapping methods
	# Each DocType pair has a specific mapper method in the app module
	mapper_methods = {
		("Sales Order", "Delivery Note"): "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
		("Sales Order", "Sales Invoice"): "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
		("Sales Order", "Purchase Order"): "erpnext.selling.doctype.sales_order.sales_order.make_purchase_order",
		("Sales Order", "Material Request"): "erpnext.selling.doctype.sales_order.sales_order.make_material_request",
		("Delivery Note", "Sales Invoice"): "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
		("Purchase Order", "Purchase Receipt"): "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
		("Purchase Order", "Purchase Invoice"): "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice",
		("Purchase Receipt", "Purchase Invoice"): "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
		("Quotation", "Sales Order"): "erpnext.selling.doctype.quotation.quotation.make_sales_order",
		("Supplier Quotation", "Purchase Order"): "erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order",
		("Material Request", "Purchase Order"): "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
		("BOM", "Work Order"): "erpnext.manufacturing.doctype.bom.bom.make_work_order",
	}

	key = (source_doctype, target_doctype)
	if key not in mapper_methods:
		return {
			"success": False,
			"error": f"No mapping defined from {source_doctype} to {target_doctype}. Available mappings: {', '.join(f'{s}→{t}' for s, t in mapper_methods.keys())}",
		}

	method = mapper_methods[key]
	target_doc = frappe.call(method, source_name)

	if isinstance(target_doc, str):
		target_doc = frappe.parse_json(target_doc)
		target_doc = frappe.get_doc(target_doc)

	if hasattr(target_doc, "insert"):
		target_doc.insert()
		frappe.db.commit()
		return {
			"success": True,
			"source": {"doctype": source_doctype, "name": source_name},
			"target": {"doctype": target_doctype, "name": target_doc.name},
			"data": target_doc.as_dict(),
		}

	return {"success": False, "error": "Failed to create mapped document"}


# ──────────────────────────────────────────────
# 11-13: Bulk Operations
# ──────────────────────────────────────────────

@_register({
	"name": "bulk_create",
	"description": "Create multiple documents at once from a list of records. Use for importing data or creating batch entries.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"records": {"type": "array", "items": {"type": "object"}, "description": "List of record data dicts to create"},
		},
		"required": ["doctype", "records"],
	},
})
def bulk_create(doctype: str, records: list) -> dict:
	_check_access(doctype, "create")
	_check_permission(doctype, "create")

	created = []
	failed = []
	for i, record in enumerate(records):
		try:
			doc = frappe.get_doc({"doctype": doctype, **record})
			doc.insert()
			created.append(doc.name)
		except Exception as e:
			failed.append({"index": i, "error": str(e), "data": record})

	frappe.db.commit()
	return {"success": True, "created_count": len(created), "failed_count": len(failed), "created_names": created, "errors": failed}


@_register({
	"name": "bulk_update",
	"description": "Update multiple documents matching filters. Use for mass updates like 'set status to Closed on all overdue invoices'.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"filters": {"type": "object", "description": "Filter conditions to select documents"},
			"update_data": {"type": "object", "description": "Fields to update on all matched documents"},
		},
		"required": ["doctype", "filters", "update_data"],
	},
})
def bulk_update(doctype: str, filters: dict, update_data: dict) -> dict:
	_check_access(doctype, "update")
	_check_permission(doctype, "write")

	names = [row.name for row in frappe.get_list(doctype, filters=filters, fields=["name"], limit_page_length=5000)]
	updated = []
	failed = []
	for name in names:
		try:
			doc = frappe.get_doc(doctype, name)
			doc.update(update_data)
			doc.save()
			updated.append(name)
		except Exception as e:
			failed.append({"name": name, "error": str(e)})

	frappe.db.commit()
	return {"success": True, "updated_count": len(updated), "failed_count": len(failed), "updated_names": updated, "errors": failed}


@_register({
	"name": "bulk_delete",
	"description": "Delete multiple documents matching filters. Always confirm the count with the user before executing.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"filters": {"type": "object", "description": "Filter conditions to select documents to delete"},
		},
		"required": ["doctype", "filters"],
	},
})
def bulk_delete(doctype: str, filters: dict) -> dict:
	_check_access(doctype, "delete")
	_check_permission(doctype, "delete")

	names = [row.name for row in frappe.get_list(doctype, filters=filters, fields=["name"], limit_page_length=5000)]
	deleted = []
	failed = []
	for name in names:
		try:
			frappe.delete_doc(doctype, name)
			deleted.append(name)
		except Exception as e:
			failed.append({"name": name, "error": str(e)})

	frappe.db.commit()
	return {"success": True, "deleted_count": len(deleted), "failed_count": len(failed), "deleted_names": deleted, "errors": failed}


# ──────────────────────────────────────────────
# 14-16: Excel & Data Import
# ──────────────────────────────────────────────

@_register({
	"name": "parse_excel",
	"description": "Parse an uploaded Excel/CSV file and return structured data with column names and row preview. Use this BEFORE import_from_excel to let the user verify the data.",
	"parameters": {
		"type": "object",
		"properties": {
			"file_url": {"type": "string", "description": "The Frappe file URL (e.g. '/files/data.xlsx')"},
			"sheet_name": {"type": "string", "description": "Sheet name for Excel files (default: first sheet)"},
			"preview_rows": {"type": "integer", "description": "Number of rows to preview (default 5)"},
		},
		"required": ["file_url"],
	},
})
def parse_excel(file_url: str, sheet_name: str = None, preview_rows: int = 5) -> dict:
	import os

	file_path = frappe.get_site_path("public", file_url.lstrip("/"))
	if not os.path.exists(file_path):
		# Try private files
		file_path = frappe.get_site_path("private", "files", os.path.basename(file_url))

	if not os.path.exists(file_path):
		return {"success": False, "error": f"File not found: {file_url}"}

	ext = os.path.splitext(file_path)[1].lower()

	if ext in (".xlsx", ".xls"):
		import openpyxl

		wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
		ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
		rows = list(ws.iter_rows(values_only=True))
		wb.close()

		if not rows:
			return {"success": False, "error": "Empty spreadsheet"}

		columns = [str(c) if c else f"Column_{i}" for i, c in enumerate(rows[0])]
		data_rows = [dict(zip(columns, row)) for row in rows[1:]]
		preview = data_rows[:preview_rows]

		return {
			"success": True,
			"file": file_url,
			"format": "excel",
			"sheet": ws.title,
			"columns": columns,
			"total_rows": len(data_rows),
			"preview": preview,
		}

	elif ext == ".csv":
		import csv

		with open(file_path, newline="", encoding="utf-8-sig") as f:
			reader = csv.DictReader(f)
			columns = reader.fieldnames or []
			data_rows = list(reader)

		preview = data_rows[:preview_rows]
		return {
			"success": True,
			"file": file_url,
			"format": "csv",
			"columns": columns,
			"total_rows": len(data_rows),
			"preview": preview,
		}

	return {"success": False, "error": f"Unsupported file format: {ext}. Use .xlsx, .xls, or .csv"}


@_register({
	"name": "import_from_excel",
	"description": "Import rows from a parsed Excel/CSV file into a DocType. Maps columns to fields and creates documents. Use parse_excel first to preview data.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The target DocType"},
			"file_url": {"type": "string", "description": "The Frappe file URL"},
			"column_mapping": {"type": "object", "description": "Map of Excel column name → DocType field name. If not provided, columns are matched by name."},
			"sheet_name": {"type": "string", "description": "Sheet name for Excel files"},
		},
		"required": ["doctype", "file_url"],
	},
})
def import_from_excel(doctype: str, file_url: str, column_mapping: dict = None, sheet_name: str = None) -> dict:
	_check_access(doctype, "create")
	_check_permission(doctype, "create")

	# Parse the file first
	parsed = parse_excel(file_url, sheet_name, preview_rows=0)
	if not parsed.get("success"):
		return parsed

	# Re-read all data
	import os

	file_path = frappe.get_site_path("public", file_url.lstrip("/"))
	if not os.path.exists(file_path):
		file_path = frappe.get_site_path("private", "files", os.path.basename(file_url))

	ext = os.path.splitext(file_path)[1].lower()
	data_rows = []

	if ext in (".xlsx", ".xls"):
		import openpyxl

		wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
		ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
		rows = list(ws.iter_rows(values_only=True))
		wb.close()
		columns = [str(c) if c else f"Column_{i}" for i, c in enumerate(rows[0])]
		data_rows = [dict(zip(columns, row)) for row in rows[1:]]
	elif ext == ".csv":
		import csv

		with open(file_path, newline="", encoding="utf-8-sig") as f:
			data_rows = list(csv.DictReader(f))

	# Apply column mapping
	mapping = column_mapping or {}

	created = []
	failed = []
	for i, row in enumerate(data_rows):
		try:
			doc_data = {}
			for col, val in row.items():
				field = mapping.get(col, col)
				if val is not None:
					doc_data[field] = val

			doc = frappe.get_doc({"doctype": doctype, **doc_data})
			doc.insert()
			created.append(doc.name)
		except Exception as e:
			failed.append({"row": i + 2, "error": str(e), "data": row})

	frappe.db.commit()
	return {
		"success": True,
		"doctype": doctype,
		"total_rows": len(data_rows),
		"created_count": len(created),
		"failed_count": len(failed),
		"created_names": created[:20],  # Limit response size
		"errors": failed[:20],
	}


@_register({
	"name": "export_to_excel",
	"description": "Export query results to a downloadable CSV file. Returns the file URL.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"filters": {"type": "object", "description": "Filter conditions"},
			"fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to export"},
			"limit": {"type": "integer", "description": "Max records (default 500)"},
		},
		"required": ["doctype"],
	},
})
def export_to_excel(doctype: str, filters: dict = None, fields: list = None, limit: int = 500) -> dict:
	import csv
	import os

	_check_access(doctype, "read")
	_check_permission(doctype, "read")

	docs = frappe.get_list(
		doctype,
		filters=filters or {},
		fields=fields or ["*"],
		limit_page_length=min(limit, 5000),
		order_by="modified desc",
	)

	if not docs:
		return {"success": True, "message": "No records found", "count": 0}

	# Write CSV
	filename = f"{doctype.lower().replace(' ', '_')}_export_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.csv"
	file_path = frappe.get_site_path("public", "files", filename)

	with open(file_path, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=docs[0].keys())
		writer.writeheader()
		writer.writerows(docs)

	file_url = f"/files/{filename}"
	return {"success": True, "doctype": doctype, "count": len(docs), "file_url": file_url, "filename": filename}


# ──────────────────────────────────────────────
# 17-20: Reports & Analytics
# ──────────────────────────────────────────────

@_register({
	"name": "run_report",
	"description": "Execute any Frappe report (Query Report, Script Report, Custom Report) with filters. Returns columns and data rows.",
	"parameters": {
		"type": "object",
		"properties": {
			"report_name": {"type": "string", "description": "Name of the report (e.g. 'Accounts Receivable', 'Sales Analytics')"},
			"filters": {"type": "object", "description": "Report filter values"},
		},
		"required": ["report_name"],
	},
})
def run_report(report_name: str, filters: dict = None) -> dict:
	from frappe.desk.query_report import run as run_query_report

	result = run_query_report(report_name, filters=filters or {})
	columns = result.get("columns", [])
	data = result.get("result", [])

	# Limit data size for LLM context
	if len(data) > 200:
		data = data[:200]
		truncated = True
	else:
		truncated = False

	return {
		"success": True,
		"report": report_name,
		"columns": columns,
		"data": data,
		"row_count": len(data),
		"truncated": truncated,
	}


@_register({
	"name": "get_dashboard_data",
	"description": "Get dashboard statistics for a DocType: total count, status breakdown, and recent records.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
		},
		"required": ["doctype"],
	},
})
def get_dashboard_data(doctype: str) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read")

	total = frappe.db.count(doctype)
	recent = frappe.get_list(doctype, fields=["name", "modified"], order_by="modified desc", limit_page_length=5)

	status_breakdown = {}
	meta = frappe.get_meta(doctype)
	if meta.has_field("status"):
		for row in frappe.get_list(doctype, fields=["status", "count(*) as cnt"], group_by="status", limit_page_length=500):
			status_breakdown[row.status] = row.cnt

	return {
		"success": True,
		"doctype": doctype,
		"total_count": total,
		"status_breakdown": status_breakdown,
		"recent_records": recent,
	}


@_register({
	"name": "get_count",
	"description": "Count documents matching filters. Lightweight alternative to get_list when you only need the count.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"filters": {"type": "object", "description": "Filter conditions"},
		},
		"required": ["doctype"],
	},
})
def get_count(doctype: str, filters: dict = None) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read")

	count = frappe.db.count(doctype, filters=filters or {})
	return {"success": True, "doctype": doctype, "count": count}


@_register({
	"name": "analyze_data",
	"description": "Retrieve data for analysis. Use this to get raw data which you can then analyze to find trends, anomalies, and insights. After getting data, provide your analysis in your response.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType to analyze"},
			"fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to include in analysis"},
			"filters": {"type": "object", "description": "Filter conditions"},
			"group_by": {"type": "string", "description": "Field to group by for aggregation"},
			"order_by": {"type": "string", "description": "Sort order"},
			"limit": {"type": "integer", "description": "Max records (default 500)"},
		},
		"required": ["doctype"],
	},
})
def analyze_data(doctype: str, fields: list = None, filters: dict = None, group_by: str = None, order_by: str = None, limit: int = 500) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read")

	kwargs = {
		"filters": filters or {},
		"fields": fields or ["*"],
		"limit_page_length": min(limit, 2000),
		"order_by": order_by or "modified desc",
	}
	if group_by:
		kwargs["group_by"] = group_by

	data = frappe.get_list(doctype, **kwargs)

	return {
		"success": True,
		"doctype": doctype,
		"count": len(data),
		"data": data,
		"hint": "Analyze this data and provide insights, trends, or anomalies to the user.",
	}


# ──────────────────────────────────────────────
# 21-24: Process Intelligence
# ──────────────────────────────────────────────

@_register({
	"name": "get_linked_documents",
	"description": "Get all documents linked to a given document (upstream and downstream). Shows the full document chain, e.g., for a Delivery Note: which Sales Order it came from, and which Sales Invoice was created from it.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "The document name/ID"},
		},
		"required": ["doctype", "name"],
	},
})
def get_linked_documents(doctype: str, name: str) -> dict:
	_check_access(doctype, "read")
	_check_permission(doctype, "read", name)

	from frappe.desk.form.linked_with import get_linked_docs, get_linked_doctypes

	linked_doctypes = get_linked_doctypes(doctype)
	linked_docs = get_linked_docs(doctype, name, linked_doctypes)

	# Flatten the results
	result = {}
	for dt, docs in linked_docs.items():
		if docs:
			result[dt] = [{"name": d.get("name"), "status": d.get("status", ""), "docstatus": d.get("docstatus", 0)} for d in docs]

	return {"success": True, "doctype": doctype, "name": name, "linked_documents": result}


@_register({
	"name": "get_workflow_info",
	"description": "Get workflow information for a DocType or specific document. Shows workflow states, transitions, and the current state.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
			"name": {"type": "string", "description": "Optional: specific document to get current workflow state"},
		},
		"required": ["doctype"],
	},
})
def get_workflow_info(doctype: str, name: str = None) -> dict:
	_check_access(doctype, "read")

	# Check if workflow exists for this doctype
	workflow_name = frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1}, "name")

	if not workflow_name:
		return {"success": True, "has_workflow": False, "message": f"No active workflow for {doctype}"}

	workflow = frappe.get_doc("Workflow", workflow_name)
	states = [{"state": s.state, "doc_status": s.doc_status, "allow_edit": s.allow_edit} for s in workflow.states]
	transitions = [{"state": t.state, "action": t.action, "next_state": t.next_state, "allowed": t.allowed} for t in workflow.transitions]

	result = {
		"success": True,
		"has_workflow": True,
		"workflow_name": workflow_name,
		"states": states,
		"transitions": transitions,
	}

	if name:
		_check_permission(doctype, "read", name)
		doc = frappe.get_doc(doctype, name)
		current_state = doc.get("workflow_state")
		available_actions = [t for t in transitions if t["state"] == current_state]
		result["current_state"] = current_state
		result["available_actions"] = available_actions

	return result


@_register({
	"name": "get_pending_approvals",
	"description": "Get all documents pending the current user's approval across all workflows. Shows what needs attention right now.",
	"parameters": {
		"type": "object",
		"properties": {},
	},
})
def get_pending_approvals() -> dict:
	user = frappe.session.user
	user_roles = frappe.get_roles(user)

	# Find all active workflows
	workflows = frappe.get_all("Workflow", filters={"is_active": 1}, fields=["name", "document_type"])

	pending = []
	for wf in workflows:
		workflow = frappe.get_doc("Workflow", wf.name)

		# Find states where the current user's roles can act
		actionable_states = set()
		for t in workflow.transitions:
			if t.allowed in user_roles:
				actionable_states.add(t.state)

		if not actionable_states:
			continue

		# Find documents in those states
		for state in actionable_states:
			try:
				docs = frappe.get_list(
					wf.document_type,
					filters={"workflow_state": state, "docstatus": ["<", 2]},
					fields=["name", "workflow_state", "modified", "owner"],
					limit_page_length=20,
				)
				for doc in docs:
					doc["doctype"] = wf.document_type
					doc["workflow"] = wf.name
					pending.append(doc)
			except Exception:
				continue

	return {"success": True, "pending_count": len(pending), "pending_approvals": pending}


@_register({
	"name": "get_doctype_meta",
	"description": "Get detailed metadata for a DocType: fields, field types, required fields, link fields, naming rules. Useful for understanding a DocType's structure before creating or updating documents.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {"type": "string", "description": "The DocType name"},
		},
		"required": ["doctype"],
	},
})
def get_doctype_meta(doctype: str) -> dict:
	_check_access(doctype, "read")

	meta = frappe.get_meta(doctype)

	fields = []
	for df in meta.fields:
		if df.fieldtype in ("Section Break", "Column Break", "Tab Break"):
			continue
		field_info = {
			"fieldname": df.fieldname,
			"label": df.label,
			"fieldtype": df.fieldtype,
			"required": bool(df.reqd),
		}
		if df.options:
			field_info["options"] = df.options
		if df.default:
			field_info["default"] = df.default
		fields.append(field_info)

	return {
		"success": True,
		"doctype": doctype,
		"is_submittable": bool(meta.is_submittable),
		"is_tree": bool(meta.is_tree),
		"autoname": meta.autoname,
		"title_field": meta.title_field,
		"fields": fields,
		"required_fields": [f for f in fields if f["required"]],
	}


# ──────────────────────────────────────────────
# 25-26: Automation & Search
# ──────────────────────────────────────────────

@_register({
	"name": "execute_automation_chain",
	"description": "Run a pre-built automation chain by name. Automation chains are sequences of steps with variable passing between them.",
	"parameters": {
		"type": "object",
		"properties": {
			"chain_name": {"type": "string", "description": "Name of the automation chain to execute"},
			"variables": {"type": "object", "description": "Initial variables to pass to the chain"},
		},
		"required": ["chain_name"],
	},
})
def execute_automation_chain(chain_name: str, variables: dict = None) -> dict:
	from mcp_ui.api.automation_chains import execute_chain

	result = execute_chain(chain_name, initial_data=json.dumps(variables or {}))
	if isinstance(result, str):
		result = json.loads(result)
	return result


@_register({
	"name": "web_search",
	"description": "Search the internet using DuckDuckGo. Use for questions about concepts, documentation, or anything outside the Frappe system.",
	"parameters": {
		"type": "object",
		"properties": {
			"query": {"type": "string", "description": "The search query"},
			"max_results": {"type": "integer", "description": "Max results (default 5)"},
		},
		"required": ["query"],
	},
})
def web_search(query: str, max_results: int = 5) -> dict:
	try:
		from duckduckgo_search import DDGS

		with DDGS() as ddgs:
			results = list(ddgs.text(query, max_results=min(max_results, 10)))

		return {
			"success": True,
			"query": query,
			"results": [{"title": r.get("title", ""), "body": r.get("body", ""), "url": r.get("href", "")} for r in results],
		}
	except Exception as e:
		return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────
# 27-29. Module/Form/Process Intelligence
# ──────────────────────────────────────────────

@_register({
	"name": "get_module_context",
	"description": "Load full context for a Frappe module — all DocTypes, required fields, workflows, transitions. "
	"Call this FIRST when discussing a specific business area (HR, Recruitment, Projects, Selling, Buying, etc.) "
	"to understand what DocTypes exist and how to work with them.",
	"parameters": {
		"type": "object",
		"properties": {
			"module": {
				"type": "string",
				"description": "The Frappe module name (e.g. 'HR', 'Recruitment', 'Projects', 'Selling', 'Buying', 'Stock', 'Accounts')"
			}
		},
		"required": ["module"],
	},
})
def tool_get_module_context(module: str) -> dict:
	from mcp_ui.openclaw.server import get_module_context
	return get_module_context(module)


@_register({
	"name": "get_form_guidance",
	"description": "Get detailed form-filling guidance for a DocType — every field organized by section, "
	"required fields, valid options for Select/Link fields, current values (if editing), "
	"workflow state and next actions. Use this BEFORE creating or updating documents to show "
	"the user exactly what fields need to be filled.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {
				"type": "string",
				"description": "The DocType to get form guidance for (e.g. 'Sales Order', 'Leave Application')"
			},
			"doc_name": {
				"type": "string",
				"description": "Optional: name of existing document to include current values and workflow state"
			}
		},
		"required": ["doctype"],
	},
})
def tool_get_form_guidance(doctype: str, doc_name: str = "") -> dict:
	from mcp_ui.openclaw.server import get_form_guidance
	return get_form_guidance(doctype, doc_name)


@_register({
	"name": "get_process_chain",
	"description": "Get the full document chain for a document — upstream parents and downstream children. "
	"Shows the complete business process flow: e.g. Quotation → Sales Order → Delivery Note → Sales Invoice "
	"with status of each linked document. Also suggests next actions. "
	"Use this to understand where a document sits in the business process.",
	"parameters": {
		"type": "object",
		"properties": {
			"doctype": {
				"type": "string",
				"description": "The DocType (e.g. 'Sales Order', 'Purchase Order')"
			},
			"doc_name": {
				"type": "string",
				"description": "The document name (e.g. 'SO-00001')"
			}
		},
		"required": ["doctype", "doc_name"],
	},
})
def tool_get_process_chain(doctype: str, doc_name: str) -> dict:
	from mcp_ui.openclaw.server import get_process_chain
	return get_process_chain(doctype, doc_name)
