"""
OpenClaw MCP Server for Frappe
Standalone stdio MCP server that OpenClaw spawns as a child process.
Connects directly to Frappe DB (like a background job) — same permission model.

Features:
- All 26 business automation tools
- Module-aware: loads DocType meta per module context
- Workflow-intelligent: understands approval chains
- Form-aware: shows field info, required fields, workflow states

Usage:
  python -m mcp_ui.openclaw

Environment variables:
  FRAPPE_SITE     — Frappe site name (default: site1.local)
  FRAPPE_BENCH    — Path to frappe-bench directory
  FRAPPE_USER     — Default user (default: Administrator)
"""
import json
import os
import sys
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
	Tool,
	TextContent,
)

logger = logging.getLogger("openclaw-frappe")

# ── Frappe initialization ───────────────────────────────────────────
def init_frappe():
	"""Initialize Frappe framework for standalone execution."""
	bench_path = os.environ.get("FRAPPE_BENCH", "")
	site = os.environ.get("FRAPPE_SITE", "site1.local")

	if bench_path:
		sys.path.insert(0, os.path.join(bench_path, "apps", "frappe"))
		os.chdir(bench_path)

	import frappe
	frappe.init(site=site, sites_path=os.path.join(bench_path, "sites") if bench_path else None)
	frappe.connect()
	frappe.set_user(os.environ.get("FRAPPE_USER", "Administrator"))
	return frappe


# ── Module context builder ──────────────────────────────────────────
def get_module_context(module_name: str) -> dict:
	"""Build rich context for a Frappe module — DocTypes, workflows, key fields."""
	import frappe

	context = {"module": module_name, "doctypes": []}
	doctypes = frappe.get_all(
		"DocType",
		filters={"module": module_name, "istable": 0, "custom": 0},
		fields=["name", "description"],
		order_by="name",
		limit=50,
	)

	for dt in doctypes:
		meta = frappe.get_meta(dt.name)
		dt_info = {
			"name": dt.name,
			"description": dt.description or "",
			"is_submittable": meta.is_submittable,
			"title_field": meta.title_field or "name",
			"required_fields": [
				{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype}
				for f in meta.fields if f.reqd and f.fieldtype not in ("Section Break", "Column Break", "Tab Break")
			],
			"key_fields": [
				{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype, "options": f.options or ""}
				for f in meta.fields
				if f.fieldtype in ("Link", "Select", "Currency", "Date", "Datetime", "Check")
				and not f.hidden and f.fieldname not in ("amended_from",)
			][:15],
			"has_workflow": bool(frappe.get_all("Workflow", filters={"document_type": dt.name, "is_active": 1}, limit=1)),
		}

		# Get workflow states if exists
		if dt_info["has_workflow"]:
			try:
				workflow = frappe.get_all(
					"Workflow",
					filters={"document_type": dt.name, "is_active": 1},
					limit=1,
				)
				if workflow:
					wf = frappe.get_doc("Workflow", workflow[0].name)
					dt_info["workflow_states"] = [s.state for s in wf.states]
					dt_info["workflow_transitions"] = [
						{"from": t.state, "to": t.next_state, "action": t.action, "allowed": t.allowed}
						for t in wf.transitions
					]
			except Exception:
				pass

		context["doctypes"].append(dt_info)

	return context


def get_form_guidance(doctype: str, doc_name: str = "") -> dict:
	"""Get detailed form guidance for creating/editing a document.

	Returns: required fields, valid options for Link/Select fields,
	current workflow state and next actions, field descriptions.
	"""
	import frappe

	meta = frappe.get_meta(doctype)
	guidance = {
		"doctype": doctype,
		"is_submittable": meta.is_submittable,
		"naming_rule": meta.autoname or "hash",
		"title_field": meta.title_field or "name",
		"sections": [],
	}

	# Build section-by-section field guide
	current_section = {"label": "Details", "fields": []}
	for f in meta.fields:
		if f.fieldtype == "Section Break":
			if current_section["fields"]:
				guidance["sections"].append(current_section)
			current_section = {"label": f.label or "Details", "fields": []}
			continue
		if f.fieldtype in ("Column Break", "Tab Break"):
			continue
		if f.hidden or f.fieldtype in ("HTML", "Fold", "Heading"):
			continue

		field_info = {
			"fieldname": f.fieldname,
			"label": f.label or f.fieldname,
			"fieldtype": f.fieldtype,
			"required": bool(f.reqd),
		}
		if f.description:
			field_info["description"] = f.description
		if f.default:
			field_info["default"] = f.default

		# For Select fields, show all options
		if f.fieldtype == "Select" and f.options:
			field_info["options"] = [o for o in f.options.split("\n") if o.strip()]

		# For Link fields, show recent/common values
		if f.fieldtype == "Link" and f.options:
			field_info["link_doctype"] = f.options
			try:
				recent = frappe.get_all(
					f.options,
					fields=["name"],
					order_by="modified desc",
					limit=10,
				)
				field_info["recent_values"] = [r.name for r in recent]
			except Exception:
				pass

		current_section["fields"].append(field_info)

	if current_section["fields"]:
		guidance["sections"].append(current_section)

	# If editing an existing doc, include current values + workflow
	if doc_name:
		try:
			doc = frappe.get_doc(doctype, doc_name)
			guidance["current_values"] = {
				f.fieldname: doc.get(f.fieldname)
				for f in meta.fields
				if f.fieldtype not in ("Section Break", "Column Break", "Tab Break", "HTML", "Fold", "Heading")
				and not f.hidden and doc.get(f.fieldname) is not None
			}
			guidance["docstatus"] = doc.docstatus
			guidance["workflow_state"] = doc.get("workflow_state", "")
		except Exception:
			pass

	# Workflow info
	workflows = frappe.get_all("Workflow", filters={"document_type": doctype, "is_active": 1}, limit=1)
	if workflows:
		try:
			wf = frappe.get_doc("Workflow", workflows[0].name)
			guidance["workflow"] = {
				"name": wf.name,
				"states": [{"state": s.state, "style": s.style or "", "doc_status": s.doc_status} for s in wf.states],
				"transitions": [
					{"from": t.state, "to": t.next_state, "action": t.action, "allowed": t.allowed}
					for t in wf.transitions
				],
			}
			if doc_name and guidance.get("workflow_state"):
				current_state = guidance["workflow_state"]
				guidance["workflow"]["next_actions"] = [
					{"action": t.action, "next_state": t.next_state, "allowed_role": t.allowed}
					for t in wf.transitions if t.state == current_state
				]
		except Exception:
			pass

	return guidance


def get_process_chain(doctype: str, doc_name: str) -> dict:
	"""Get the full document chain — upstream (parents) and downstream (children).

	Shows: Quotation → Sales Order → Delivery Note → Sales Invoice
	with status of each linked document.
	"""
	import frappe

	chain = {
		"doctype": doctype,
		"name": doc_name,
		"upstream": [],
		"downstream": [],
	}

	try:
		doc = frappe.get_doc(doctype, doc_name)
		chain["status"] = doc.get("status", doc.get("workflow_state", ""))
		chain["docstatus"] = doc.docstatus

		# Common upstream link fields
		upstream_fields = {
			"Delivery Note": [("Sales Order", "against_sales_order")],
			"Sales Invoice": [("Sales Order", "sales_order"), ("Delivery Note", "delivery_note")],
			"Purchase Receipt": [("Purchase Order", "purchase_order")],
			"Purchase Invoice": [("Purchase Order", "purchase_order"), ("Purchase Receipt", "purchase_receipt")],
			"Sales Order": [("Quotation", "prevdoc_docname")],
			"Purchase Order": [("Supplier Quotation", "supplier_quotation"), ("Material Request", "material_request")],
			"Work Order": [("BOM", "bom_no"), ("Sales Order", "sales_order")],
			"Stock Entry": [("Work Order", "work_order"), ("Purchase Receipt", "purchase_receipt")],
		}

		# Check items table for upstream links
		if hasattr(doc, "items"):
			seen = set()
			for item in doc.items:
				for link_dt, link_field in upstream_fields.get(doctype, []):
					val = item.get(link_field)
					if val and val not in seen:
						seen.add(val)
						try:
							link_doc = frappe.get_doc(link_dt, val)
							chain["upstream"].append({
								"doctype": link_dt,
								"name": val,
								"status": link_doc.get("status", ""),
								"docstatus": link_doc.docstatus,
							})
						except Exception:
							chain["upstream"].append({"doctype": link_dt, "name": val, "status": "unknown"})

		# Also check top-level fields
		for link_dt, link_field in upstream_fields.get(doctype, []):
			val = doc.get(link_field)
			if val and not any(u["name"] == val for u in chain["upstream"]):
				try:
					link_doc = frappe.get_doc(link_dt, val)
					chain["upstream"].append({
						"doctype": link_dt,
						"name": val,
						"status": link_doc.get("status", ""),
						"docstatus": link_doc.docstatus,
					})
				except Exception:
					pass

		# Get downstream linked documents
		downstream_map = {
			"Quotation": ["Sales Order"],
			"Sales Order": ["Delivery Note", "Sales Invoice", "Work Order"],
			"Delivery Note": ["Sales Invoice"],
			"Purchase Order": ["Purchase Receipt", "Purchase Invoice"],
			"Purchase Receipt": ["Purchase Invoice"],
			"Material Request": ["Purchase Order", "Stock Entry"],
			"BOM": ["Work Order"],
			"Work Order": ["Stock Entry", "Job Card"],
		}

		for child_dt in downstream_map.get(doctype, []):
			try:
				# Search items tables for references back to this doc
				linked = frappe.get_all(
					child_dt,
					filters={"docstatus": ["<", 2]},
					fields=["name", "status", "docstatus"],
					limit=10,
				)
				# Filter to those actually linked
				meta_child = frappe.get_meta(child_dt)
				link_fieldnames = [f.fieldname for f in meta_child.fields if f.fieldtype == "Link" and f.options == doctype]
				for link_fn in link_fieldnames:
					direct = frappe.get_all(
						child_dt,
						filters={link_fn: doc_name, "docstatus": ["<", 2]},
						fields=["name", "status", "docstatus"],
						limit=10,
					)
					for d in direct:
						if not any(dd["name"] == d.name for dd in chain["downstream"]):
							chain["downstream"].append({
								"doctype": child_dt,
								"name": d.name,
								"status": d.get("status", ""),
								"docstatus": d.docstatus,
							})
			except Exception:
				pass

		# Suggest next actions
		chain["suggested_next"] = []
		if doc.docstatus == 0:
			chain["suggested_next"].append(f"Submit {doctype} {doc_name}")
		elif doc.docstatus == 1:
			for child_dt in downstream_map.get(doctype, []):
				has_child = any(d["doctype"] == child_dt for d in chain["downstream"])
				if not has_child:
					chain["suggested_next"].append(f"Create {child_dt} from {doctype} {doc_name} (use make_mapped_document)")

	except frappe.DoesNotExistError:
		chain["error"] = f"{doctype} {doc_name} does not exist"
	except frappe.PermissionError:
		chain["error"] = "You don't have permission to access this document"

	return chain


def build_system_prompt(frappe_module) -> str:
	"""Build module-aware system prompt with Frappe context."""
	frappe = frappe_module

	user = frappe.session.user
	user_doc = frappe.get_doc("User", user)
	user_name = user_doc.full_name or user
	user_roles = [r.role for r in user_doc.roles]
	installed_apps = frappe.get_installed_apps()

	# Get all modules
	modules = frappe.get_all("Module Def", fields=["name"], order_by="name")
	module_list = [m.name for m in modules]

	# Get company
	try:
		company = frappe.db.get_single_value("Global Defaults", "default_company") or "Your Company"
	except Exception:
		company = "Your Company"

	return f"""You are a business automation engine for {company}'s Frappe/ERPNext system, connected via Telegram.
You don't just answer questions — you EXECUTE business processes end-to-end.

CAPABILITIES:
- Run full business process chains: Quotation → SO → DN → SI (use make_mapped_document)
- Create, read, update, delete any document the user has permission for
- Submit, cancel, amend documents with workflow awareness
- Bulk operations (create/update/delete)
- Run reports and analyze data
- Import/export Excel files
- Search the web
- Track document chains and linked documents

MODULE AWARENESS:
When a user asks about a specific area (HR, Recruitment, Projects, etc.), FIRST use get_module_context
to load the module's DocTypes, fields, and workflows. This gives you:
- All DocTypes in the module with their required fields
- Active workflows with states and transitions
- Key fields (Links, Selects, etc.) for proper form guidance

WORKFLOW GUIDANCE:
- Before creating downstream docs, ALWAYS check upstream doc status
- Use make_mapped_document for SO→DN, DN→SI, PO→PR chains
- When a DocType has a workflow, tell the user about required states/approvals
- Show what fields need to be filled and what the next workflow action is

FORM GUIDANCE:
When users want to create or modify documents, show them:
1. Required fields they MUST fill
2. Key fields they SHOULD fill
3. Current workflow state and next available actions
4. Link field options (what values are valid)

RESPONSE FORMAT (Telegram):
- Keep responses concise — Telegram messages have character limits
- Use bullet points and bold for key info
- For tables, use simple formatting (not markdown tables)
- Show document links as: [DocType: Name]
- Confirm before bulk operations (>5 records)

SECURITY:
- Never reveal salary, compensation, or personal financial data of other users
- Never share passwords, API keys, or bank details
- If permission denied, say "You don't have access" without revealing the data

Available modules: {', '.join(module_list[:20])}
Current user: {user_name} (Roles: {', '.join(user_roles)})
Installed apps: {', '.join(installed_apps)}"""


# ── MCP Server ──────────────────────────────────────────────────────
def create_server(frappe_module) -> Server:
	"""Create the MCP server with all Frappe tools."""
	frappe = frappe_module
	server = Server("frappe-mcp")

	# Import the tool functions
	from mcp_ui.ai.tools import get_tool_schemas, get_tool_map

	tool_map = get_tool_map()
	tool_schemas = get_tool_schemas()

	# No extra tools — all 29 tools are now in ai/tools.py
	extra_tools = []

	@server.list_tools()
	async def list_tools() -> list[Tool]:
		"""List all available tools."""
		tools = []
		for ts in tool_schemas:
			fn = ts["function"]
			tools.append(Tool(
				name=fn["name"],
				description=fn["description"],
				inputSchema=fn["parameters"],
			))
		tools.extend(extra_tools)
		return tools

	@server.call_tool()
	async def call_tool(name: str, arguments: dict) -> list[TextContent]:
		"""Execute a Frappe tool."""
		try:
			# Look up the tool function
			fn = tool_map.get(name)
			if not fn:
				return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

			# Execute with proper user context
			user = os.environ.get("FRAPPE_USER", "Administrator")
			frappe.set_user(user)

			result = fn(**arguments)

			# Ensure result is JSON serializable
			result_str = json.dumps(result, default=str, indent=2)
			return [TextContent(type="text", text=result_str)]

		except frappe.PermissionError as e:
			return [TextContent(type="text", text=json.dumps({"error": f"Permission denied: {str(e)}"}))]
		except Exception as e:
			logger.exception(f"Tool {name} failed")
			return [TextContent(type="text", text=json.dumps({"error": f"Tool execution failed: {str(e)}"}))]

	return server


async def run():
	"""Main entry point — initialize Frappe and start MCP server."""
	frappe = init_frappe()
	logger.info(f"Frappe initialized: site={frappe.local.site}, user={frappe.session.user}")

	server = create_server(frappe)

	async with stdio_server() as (read_stream, write_stream):
		await server.run(read_stream, write_stream, server.create_initialization_options())
