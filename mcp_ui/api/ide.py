import frappe
import json


# ---------------------------------------------------------------------------
# 1. Capability Detection
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_capabilities():
	"""Check what the current site/user is allowed to do."""
	site_config = frappe.get_site_config()
	server_scripts_enabled = bool(site_config.get("server_script_enabled"))
	has_script_manager = "Script Manager" in frappe.get_roles()
	user_roles = frappe.get_roles()

	return {
		"success": True,
		"server_scripts_enabled": server_scripts_enabled,
		"has_script_manager": has_script_manager,
		"user_roles": user_roles,
	}


# ---------------------------------------------------------------------------
# 2. Client Scripts CRUD
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_client_scripts(doctype=None):
	"""List all Client Scripts, optionally filtered by dt."""
	filters = {}
	if doctype:
		filters["dt"] = doctype

	scripts = frappe.get_all(
		"Client Script",
		filters=filters,
		fields=["name", "dt", "view", "enabled", "module", "modified"],
		order_by="modified desc",
	)

	return {"success": True, "scripts": scripts}


@frappe.whitelist()
def get_client_script(name):
	"""Get a single Client Script with full script code."""
	doc = frappe.get_doc("Client Script", name)
	return {
		"success": True,
		"script": {
			"name": doc.name,
			"dt": doc.dt,
			"view": doc.view,
			"enabled": doc.enabled,
			"script": doc.script,
			"module": doc.module,
			"modified": doc.modified,
		},
	}


@frappe.whitelist()
def save_client_script(name=None, dt=None, view="Form", enabled=1, script="", module=None):
	"""Create or update a Client Script."""
	if name and frappe.db.exists("Client Script", name):
		doc = frappe.get_doc("Client Script", name)
		if dt:
			doc.dt = dt
		doc.view = view
		doc.enabled = int(enabled)
		doc.script = script
		if module is not None:
			doc.module = module
		doc.save()
	else:
		doc = frappe.new_doc("Client Script")
		if name:
			doc.name = name
		doc.dt = dt
		doc.view = view
		doc.enabled = int(enabled)
		doc.script = script
		if module is not None:
			doc.module = module
		doc.insert()

	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"message": "Client Script saved successfully",
	}


@frappe.whitelist()
def delete_client_script(name):
	"""Delete a Client Script."""
	frappe.delete_doc("Client Script", name)
	frappe.db.commit()

	return {"success": True, "message": f"Client Script '{name}' deleted"}


# ---------------------------------------------------------------------------
# 3. Server Scripts CRUD
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_server_scripts(doctype=None, script_type=None):
	"""List all Server Scripts, optionally filtered by doctype or script_type."""
	filters = {}
	if doctype:
		filters["reference_doctype"] = doctype
	if script_type:
		filters["script_type"] = script_type

	scripts = frappe.get_all(
		"Server Script",
		filters=filters,
		fields=[
			"name", "script_type", "reference_doctype", "doctype_event",
			"api_method", "disabled", "module", "modified",
		],
		order_by="modified desc",
	)

	return {"success": True, "scripts": scripts}


@frappe.whitelist()
def get_server_script(name):
	"""Get a single Server Script with full code."""
	doc = frappe.get_doc("Server Script", name)
	return {
		"success": True,
		"script": {
			"name": doc.name,
			"script_type": doc.script_type,
			"reference_doctype": doc.reference_doctype,
			"doctype_event": doc.doctype_event,
			"api_method": doc.api_method,
			"script": doc.script,
			"disabled": doc.disabled,
			"event_frequency": doc.event_frequency,
			"cron_format": doc.cron_format,
			"allow_guest": doc.allow_guest,
			"module": doc.module,
			"modified": doc.modified,
		},
	}


@frappe.whitelist()
def save_server_script(
	name=None,
	script_type=None,
	reference_doctype=None,
	doctype_event=None,
	api_method=None,
	script="",
	disabled=0,
	event_frequency=None,
	cron_format=None,
	allow_guest=0,
	module=None,
):
	"""Create or update a Server Script."""
	if name and frappe.db.exists("Server Script", name):
		doc = frappe.get_doc("Server Script", name)
		if script_type is not None:
			doc.script_type = script_type
		if reference_doctype is not None:
			doc.reference_doctype = reference_doctype
		if doctype_event is not None:
			doc.doctype_event = doctype_event
		if api_method is not None:
			doc.api_method = api_method
		doc.script = script
		doc.disabled = int(disabled)
		if event_frequency is not None:
			doc.event_frequency = event_frequency
		if cron_format is not None:
			doc.cron_format = cron_format
		doc.allow_guest = int(allow_guest)
		if module is not None:
			doc.module = module
		doc.save()
	else:
		doc = frappe.new_doc("Server Script")
		if name:
			doc.name = name
		doc.script_type = script_type
		doc.reference_doctype = reference_doctype
		doc.doctype_event = doctype_event
		doc.api_method = api_method
		doc.script = script
		doc.disabled = int(disabled)
		doc.event_frequency = event_frequency
		doc.cron_format = cron_format
		doc.allow_guest = int(allow_guest)
		if module is not None:
			doc.module = module
		doc.insert()

	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"message": "Server Script saved successfully",
	}


@frappe.whitelist()
def delete_server_script(name):
	"""Delete a Server Script."""
	frappe.delete_doc("Server Script", name)
	frappe.db.commit()

	return {"success": True, "message": f"Server Script '{name}' deleted"}


# ---------------------------------------------------------------------------
# 4. Workflows CRUD
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_frappe_workflows():
	"""List all Workflows with their states and transitions (child tables)."""
	workflows = frappe.get_all(
		"Workflow",
		fields=["name", "document_type", "is_active", "modified"],
		order_by="modified desc",
	)

	for wf in workflows:
		wf["states"] = frappe.get_all(
			"Workflow Document State",
			filters={"parent": wf["name"]},
			fields=["state", "doc_status", "is_optional_state", "allow_edit", "idx"],
			order_by="idx asc",
		)
		wf["transitions"] = frappe.get_all(
			"Workflow Transition",
			filters={"parent": wf["name"]},
			fields=["state", "action", "next_state", "allowed", "condition", "idx"],
			order_by="idx asc",
		)

	return {"success": True, "workflows": workflows}


@frappe.whitelist()
def save_workflow(workflow_name, document_type, is_active=1, states=None, transitions=None):
	"""Create or update a Workflow.

	Automatically creates missing Workflow State and Workflow Action Master
	records so the caller does not need to pre-create them.
	"""
	states = json.loads(states) if isinstance(states, str) else (states or [])
	transitions = json.loads(transitions) if isinstance(transitions, str) else (transitions or [])

	# --- ensure Workflow State records exist --------------------------------
	all_state_names = set()
	for s in states:
		all_state_names.add(s.get("state"))
	for t in transitions:
		all_state_names.add(t.get("state"))
		all_state_names.add(t.get("next_state"))
	all_state_names.discard(None)

	for state_name in all_state_names:
		if not frappe.db.exists("Workflow State", state_name):
			ws = frappe.new_doc("Workflow State")
			ws.workflow_state_name = state_name
			ws.insert(ignore_permissions=True)

	# --- ensure Workflow Action Master records exist ------------------------
	all_actions = {t.get("action") for t in transitions}
	all_actions.discard(None)

	for action_name in all_actions:
		if not frappe.db.exists("Workflow Action Master", action_name):
			wa = frappe.new_doc("Workflow Action Master")
			wa.workflow_action_name = action_name
			wa.insert(ignore_permissions=True)

	# --- create or update the Workflow itself -------------------------------
	if frappe.db.exists("Workflow", workflow_name):
		doc = frappe.get_doc("Workflow", workflow_name)
		doc.document_type = document_type
		doc.is_active = int(is_active)
	else:
		doc = frappe.new_doc("Workflow")
		doc.workflow_name = workflow_name
		doc.document_type = document_type
		doc.is_active = int(is_active)

	# rebuild child tables
	doc.states = []
	for s in states:
		doc.append("states", {
			"state": s.get("state"),
			"doc_status": s.get("doc_status", "0"),
			"is_optional_state": s.get("is_optional_state", 0),
			"allow_edit": s.get("allow_edit", "All"),
		})

	doc.transitions = []
	for t in transitions:
		doc.append("transitions", {
			"state": t.get("state"),
			"action": t.get("action"),
			"next_state": t.get("next_state"),
			"allowed": t.get("allowed", "All"),
			"condition": t.get("condition", ""),
		})

	if frappe.db.exists("Workflow", workflow_name):
		doc.save()
	else:
		doc.insert()

	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"message": "Workflow saved successfully",
	}


@frappe.whitelist()
def delete_workflow(name):
	"""Delete a Workflow."""
	frappe.delete_doc("Workflow", name)
	frappe.db.commit()

	return {"success": True, "message": f"Workflow '{name}' deleted"}


# ---------------------------------------------------------------------------
# 5. Schema Management
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_custom_fields_for_doctype(doctype):
	"""List all Custom Fields for a given DocType."""
	fields = frappe.get_all(
		"Custom Field",
		filters={"dt": doctype},
		fields=[
			"name", "label", "fieldname", "fieldtype", "options",
			"insert_after", "reqd", "hidden", "default",
			"description", "modified",
		],
		order_by="idx asc",
	)

	return {"success": True, "fields": fields}


@frappe.whitelist()
def add_custom_field(
	dt,
	label,
	fieldtype,
	options=None,
	insert_after=None,
	reqd=0,
	hidden=0,
	default=None,
	description=None,
):
	"""Add a Custom Field to a DocType."""
	doc = frappe.new_doc("Custom Field")
	doc.dt = dt
	doc.label = label
	doc.fieldtype = fieldtype
	if options is not None:
		doc.options = options
	if insert_after is not None:
		doc.insert_after = insert_after
	doc.reqd = int(reqd)
	doc.hidden = int(hidden)
	if default is not None:
		doc.default = default
	if description is not None:
		doc.description = description

	doc.insert()
	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"fieldname": doc.fieldname,
		"message": "Custom Field added successfully",
	}


@frappe.whitelist()
def delete_custom_field(name):
	"""Delete a Custom Field."""
	frappe.delete_doc("Custom Field", name)
	frappe.db.commit()

	return {"success": True, "message": f"Custom Field '{name}' deleted"}


@frappe.whitelist()
def get_property_setters(doctype):
	"""List all Property Setters for a given DocType."""
	setters = frappe.get_all(
		"Property Setter",
		filters={"doc_type": doctype},
		fields=[
			"name", "doc_type", "field_name", "property",
			"value", "property_type", "modified",
		],
		order_by="modified desc",
	)

	return {"success": True, "property_setters": setters}


@frappe.whitelist()
def set_property(doc_type, field_name, property, value, property_type="Data"):
	"""Create or update a Property Setter."""
	existing = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doc_type, "field_name": field_name, "property": property},
		"name",
	)

	if existing:
		doc = frappe.get_doc("Property Setter", existing)
		doc.value = value
		doc.property_type = property_type
		doc.save()
	else:
		doc = frappe.new_doc("Property Setter")
		doc.doctype_or_field = "DocField" if field_name else "DocType"
		doc.doc_type = doc_type
		doc.field_name = field_name
		doc.property = property
		doc.value = value
		doc.property_type = property_type
		doc.insert()

	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"message": "Property Setter saved successfully",
	}


# ---------------------------------------------------------------------------
# 6. Notifications
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_notifications():
	"""List all Notification rules."""
	notifications = frappe.get_all(
		"Notification",
		fields=[
			"name", "subject", "document_type", "event",
			"channel", "enabled", "modified",
		],
		order_by="modified desc",
	)

	return {"success": True, "notifications": notifications}


@frappe.whitelist()
def get_notification(name):
	"""Get a single Notification with full details."""
	doc = frappe.get_doc("Notification", name)
	return {
		"success": True,
		"notification": {
			"name": doc.name,
			"subject": doc.subject,
			"document_type": doc.document_type,
			"event": doc.event,
			"channel": doc.channel,
			"enabled": doc.enabled,
			"condition": doc.condition,
			"message": doc.message,
			"recipients": [
				{
					"receiver_by_document_field": r.receiver_by_document_field,
					"receiver_by_role": r.receiver_by_role,
					"condition": r.condition,
				}
				for r in (doc.recipients or [])
			],
			"modified": doc.modified,
		},
	}


# ---------------------------------------------------------------------------
# 7. Hooks Discovery
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_doc_events():
	"""Return registered doc_events hooks from all installed apps."""
	doc_events = frappe.get_hooks("doc_events") or {}

	return {"success": True, "doc_events": doc_events}
