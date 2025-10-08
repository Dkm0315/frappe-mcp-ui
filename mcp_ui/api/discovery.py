"""
System Discovery API
Provides information about installed apps, DocTypes, and customizations
"""
import frappe
from mcp_ui.utils.app_checker import is_nextai_installed


@frappe.whitelist()
def get_installed_apps():
	"""Get all installed Frappe apps with metadata"""
	apps = frappe.get_installed_apps()

	app_list = []
	for app in apps:
		try:
			app_info = {
				"name": app,
				"title": frappe.get_hooks("app_title", app_name=app) or [app],
				"modules": frappe.get_module_list(app) if app != "frappe" else [],
			}
			app_list.append(app_info)
		except Exception:
			# Skip apps that don't have proper hooks
			continue

	return {"success": True, "apps": app_list, "count": len(app_list)}


@frappe.whitelist()
def get_doctypes(app=None, module=None):
	"""
	Get DocTypes with optional filtering by app or module

	Args:
		app: Filter by app name
		module: Filter by module name
	"""
	try:
		filters = {"custom": 0, "istable": 0}

		if module:
			filters["module"] = module

		doctypes = frappe.get_all(
			"DocType",
			filters=filters,
			fields=[
				"name",
				"module",
				"is_submittable",
				"is_tree",
				"issingle",
				"editable_grid",
				"track_changes",
			],
			order_by="name asc",
		)

		# Filter by app if provided
		if app:
			doctypes = [dt for dt in doctypes if frappe.get_meta(dt['name']).module in frappe.get_module_list(app)]

		return {"success": True, "doctypes": doctypes, "count": len(doctypes)}
	except Exception as e:
		frappe.log_error(f"Error getting doctypes: {str(e)}")
		return {"success": False, "error": str(e), "doctypes": [], "count": 0}


@frappe.whitelist()
def get_custom_fields(doctype=None):
	"""
	Get custom fields for a DocType or all custom fields

	Args:
		doctype: Optional DocType name to filter
	"""
	filters = {}
	if doctype:
		filters["dt"] = doctype

	custom_fields = frappe.get_all(
		"Custom Field",
		filters=filters,
		fields=["name", "dt", "fieldname", "fieldtype", "label", "options", "insert_after"],
		order_by="dt asc, idx asc",
	)

	# Group by doctype
	grouped = {}
	for field in custom_fields:
		dt = field["dt"]
		if dt not in grouped:
			grouped[dt] = []
		grouped[dt].append(field)

	return {"success": True, "custom_fields": grouped, "count": len(custom_fields)}


@frappe.whitelist()
def get_workflows():
	"""Get active workflows in the system"""
	workflows = frappe.get_all(
		"Workflow",
		filters={"is_active": 1},
		fields=["name", "document_type", "workflow_name", "workflow_state_field"],
	)

	# Get workflow states for each workflow
	for workflow in workflows:
		states = frappe.get_all(
			"Workflow Document State",
			filters={"parent": workflow["name"]},
			fields=["state", "doc_status", "update_field", "update_value"],
			order_by="idx asc",
		)
		workflow["states"] = states

	return {"success": True, "workflows": workflows, "count": len(workflows)}


@frappe.whitelist()
def get_doctype_meta(doctype):
	"""
	Get detailed metadata for a specific DocType

	Args:
		doctype: DocType name
	"""
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(f"DocType '{doctype}' not found")

	meta = frappe.get_meta(doctype)

	# Get field information
	fields = []
	for field in meta.fields:
		fields.append(
			{
				"fieldname": field.fieldname,
				"fieldtype": field.fieldtype,
				"label": field.label,
				"reqd": field.reqd,
				"options": field.options,
				"default": field.default,
				"description": field.description,
			}
		)

	# Get permissions
	permissions = []
	for perm in meta.permissions:
		permissions.append(
			{
				"role": perm.role,
				"read": perm.read,
				"write": perm.write,
				"create": perm.create,
				"delete": perm.delete,
				"submit": perm.submit,
			}
		)

	return {
		"success": True,
		"doctype": doctype,
		"meta": {
			"name": meta.name,
			"module": meta.module,
			"is_submittable": meta.is_submittable,
			"is_tree": meta.is_tree,
			"issingle": meta.issingle,
			"track_changes": meta.track_changes,
			"fields": fields,
			"permissions": permissions,
			"title_field": meta.title_field,
			"search_fields": meta.search_fields,
		},
	}


@frappe.whitelist()
def get_system_stats():
	"""Get overall system statistics"""
	stats = {
		"total_apps": len(frappe.get_installed_apps()),
		"total_doctypes": frappe.db.count("DocType", {"custom": 0, "istable": 0}),
		"custom_doctypes": frappe.db.count("DocType", {"custom": 1}),
		"total_users": frappe.db.count("User", {"enabled": 1}),
		"total_custom_fields": frappe.db.count("Custom Field"),
		"active_workflows": frappe.db.count("Workflow", {"is_active": 1}),
	}

	return {"success": True, "stats": stats}


@frappe.whitelist()
def get_doctypes_by_module(app=None):
	"""
	Get DocTypes grouped by app and module
	Returns hierarchical structure for UI
	
	Args:
		app: Optional app name to filter
	
	Returns:
		{
			"success": True,
			"data": {
				"frappe": {
					"Core": [doctypes...],
					"Email": [doctypes...]
				},
				"erpnext": {
					"Accounts": [doctypes...],
					"Stock": [doctypes...]
				}
			},
			"has_nextai": bool
		}
	"""
	try:
		filters = {"custom": 0, "istable": 0}
		doctypes = frappe.get_all(
			"DocType",
			filters=filters,
			fields=["name", "module", "is_submittable", "issingle", "is_tree", "description"],
			order_by="module, name"
		)
		
		# Group by app and module
		grouped = {}
		for dt in doctypes:
			module_name = dt['module']
			# Get app for this module
			app_name = get_app_for_module(module_name)
			
			if app and app != app_name:
				continue
			
			if app_name not in grouped:
				grouped[app_name] = {}
			
			if module_name not in grouped[app_name]:
				grouped[app_name][module_name] = []
			
			grouped[app_name][module_name].append(dt)
		
		return {
			"success": True,
			"data": grouped,
			"has_nextai": is_nextai_installed()
		}
	except Exception as e:
		frappe.log_error(f"Error getting doctypes by module: {str(e)}")
		return {
			"success": False,
			"error": str(e),
			"data": {},
			"has_nextai": False
		}


def get_app_for_module(module_name):
	"""
	Map module to app
	
	Args:
		module_name: Module name
		
	Returns:
		App name (frappe, erpnext, nextai, etc.)
	"""
	# Frappe core modules
	frappe_modules = [
		'Core', 'Desk', 'Website', 'Email', 'Automation', 'Workflow', 'Integrations',
		'Custom', 'Printing', 'Geo', 'Social', 'Contacts', 'Utilities', 'Installer'
	]
	
	# ERPNext modules
	erpnext_modules = [
		'Accounts', 'Stock', 'Buying', 'Selling', 'Manufacturing', 'HR', 'CRM',
		'Projects', 'Support', 'Assets', 'Maintenance', 'Quality Management',
		'Setup', 'Portal', 'Loan Management', 'Healthcare', 'Education',
		'Non Profit', 'Agriculture', 'Telephony', 'E-commerce'
	]
	
	# NextAI modules
	nextai_modules = [
		'Nextai', 'Funnel', 'WhatsApp Business API Integration', 'Form Builder',
		'Password Manager', 'Personal Whatsapp Integration'
	]
	
	# MCP UI modules
	mcp_modules = ['Mcp Ui']
	
	if module_name in frappe_modules:
		return 'frappe'
	elif module_name in erpnext_modules:
		return 'erpnext'
	elif module_name in nextai_modules:
		return 'nextai'
	elif module_name in mcp_modules:
		return 'mcp_ui'
	else:
		# Try to determine from module definition
		try:
			module_def = frappe.get_module(module_name)
			if module_def and hasattr(module_def, '__name__'):
				app_name = module_def.__name__.split('.')[0]
				return app_name
		except:
			pass
		
		return 'custom'

