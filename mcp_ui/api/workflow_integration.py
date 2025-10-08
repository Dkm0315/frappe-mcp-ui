"""
Workflow Integration API
Optional integration with NextAI Funnel workflows
"""
import frappe
import json
from mcp_ui.utils.app_checker import is_nextai_installed


@frappe.whitelist()
def get_workflows(category=None):
	"""
	Get available Funnel workflows with dynamic categorization
	
	Args:
		category: Optional category filter
	
	Returns:
		{
			"success": bool,
			"workflows": {
				"category1": [],
				"category2": [],
				...
			},
			"categories": ["category1", "category2", ...],
			"total": int
		}
	"""
	if not is_nextai_installed():
		return {
			"success": False,
			"message": "NextAI not installed",
			"workflows": {},
			"categories": [],
			"total": 0
		}
	
	try:
		workflows = frappe.get_all(
			"Funnel Published",
			filters={"published": 1},
			fields=["name", "funnel", "funnel_description", "modified"],
			order_by="modified desc"
		)
		
		# Categorize workflows dynamically
		categorized = {}
		
		for wf in workflows:
			wf_category = detect_workflow_category(wf)
			
			# Filter by category if specified
			if category and wf_category != category:
				continue
			
			if wf_category not in categorized:
				categorized[wf_category] = []
			
			categorized[wf_category].append(wf)
		
		# Get all categories sorted by workflow count
		categories = sorted(categorized.keys(), key=lambda x: len(categorized[x]), reverse=True)
		
		return {
			"success": True,
			"workflows": categorized,
			"categories": categories,
			"total": len(workflows)
		}
	except Exception as e:
		frappe.log_error(f"Workflow fetch error: {str(e)}")
		return {
			"success": False,
			"message": str(e),
			"workflows": {},
			"categories": [],
			"total": 0
		}


def detect_workflow_category(workflow):
	"""
	Detect workflow category dynamically based on workflow's DocTypes and modules
	
	Args:
		workflow: Workflow dict with name and funnel_description
		
	Returns:
		Category string (module-based or keyword-based)
	"""
	try:
		# Get workflow definition to analyze which DocTypes it uses
		funnel_name = workflow.get('name')
		definitions = frappe.get_all(
			"Funnel Definition",
			filters={"parent": funnel_name, "element_type": "Trigger"},
			fields=["data"],
			limit=5
		)
		
		# Extract modules from DocTypes used in workflow
		modules_used = set()
		for defn in definitions:
			try:
				data = json.loads(defn.get('data', '{}'))
				doctype = data.get('doctype')
				if doctype:
					meta = frappe.get_meta(doctype)
					if meta and meta.module:
						modules_used.add(meta.module)
			except:
				continue
		
		# Map modules to categories
		if modules_used:
			# Manufacturing modules
			if any(m in modules_used for m in ['Manufacturing', 'Stock', 'Buying']):
				return 'manufacturing'
			# Sales modules
			if any(m in modules_used for m in ['Selling', 'Accounts', 'CRM']):
				return 'sales'
			# HR modules
			if any(m in modules_used for m in ['HR', 'Payroll']):
				return 'hr'
			# Project modules
			if any(m in modules_used for m in ['Projects', 'Support']):
				return 'projects'
			# Custom modules - use module name as category
			for module in modules_used:
				if module not in ['Core', 'Desk', 'Website', 'Email']:
					return module.lower().replace(' ', '_')
		
		# Fallback to keyword detection
		name = (workflow.get('funnel', '') + ' ' + workflow.get('funnel_description', '')).lower()
		
		if any(word in name for word in ['test', 'demo', 'sample', 'bulk', 'generate']):
			return 'testing'
		
		return 'other'
		
	except Exception as e:
		frappe.log_error(f"Error detecting workflow category: {str(e)}")
		return 'other'


@frappe.whitelist()
def trigger_workflow(funnel_name, variables=None):
	"""
	Trigger a Funnel workflow
	
	Args:
		funnel_name: Name of the Funnel Published record
		variables: JSON string of workflow variables
		
	Returns:
		{
			"success": bool,
			"workflow_id": str,
			"status": str,
			"message": str
		}
	"""
	if not is_nextai_installed():
		frappe.throw("NextAI not installed. Cannot trigger workflows.")
	
	try:
		# Import only when needed
		from nextai.funnel.doctype.funnel_task.triggers.on_manual_trigger import trigger
		
		# Parse variables
		workflow_vars = {}
		if variables:
			try:
				workflow_vars = json.loads(variables) if isinstance(variables, str) else variables
			except:
				frappe.log_error(f"Invalid workflow variables: {variables}")
				workflow_vars = {}
		
		# Trigger the workflow
		workflow_id = trigger(
			funnel_name=funnel_name,
			variables=workflow_vars
		)
		
		return {
			"success": True,
			"workflow_id": workflow_id,
			"status": "running",
			"message": f"Workflow {funnel_name} started successfully"
		}
	except Exception as e:
		frappe.log_error(f"Workflow trigger error: {str(e)}")
		return {
			"success": False,
			"workflow_id": None,
			"status": "failed",
			"message": str(e)
		}


@frappe.whitelist()
def get_workflow_status(workflow_id):
	"""
	Get Funnel workflow execution status
	
	Args:
		workflow_id: Funnel Workflow name
		
	Returns:
		{
			"workflow_id": str,
			"status": str (running, finished, stopped, failed),
			"variables": dict,
			"tasks": list,
			"progress": float (0-100)
		}
	"""
	if not is_nextai_installed():
		frappe.throw("NextAI not installed")
	
	try:
		workflow = frappe.get_doc("Funnel Workflow", workflow_id)
		
		# Get tasks
		tasks = frappe.get_all(
			"Funnel Task",
			filters={"workflow": workflow_id},
			fields=["name", "node_name", "status", "info", "modified"],
			order_by="modified asc"
		)
		
		progress = calculate_progress(tasks)
		
		return {
			"success": True,
			"workflow_id": workflow_id,
			"status": workflow.status,
			"variables": json.loads(workflow.variables) if workflow.variables else {},
			"tasks": tasks,
			"progress": progress,
			"funnel": workflow.funnel
		}
	except Exception as e:
		frappe.log_error(f"Workflow status error: {str(e)}")
		return {
			"success": False,
			"error": str(e),
			"workflow_id": workflow_id,
			"status": "unknown",
			"variables": {},
			"tasks": [],
			"progress": 0
		}


def calculate_progress(tasks):
	"""
	Calculate workflow progress percentage
	
	Args:
		tasks: List of task dicts with status field
		
	Returns:
		float: Progress percentage (0-100)
	"""
	if not tasks:
		return 0
	
	completed_statuses = ['completed', 'cancelled']
	completed_count = sum(1 for task in tasks if task.get('status') in completed_statuses)
	
	return round((completed_count / len(tasks)) * 100, 2)


@frappe.whitelist()
def get_builder_url(funnel_name=None):
	"""
	Get URL for NextAI Funnel builder (for iframe embedding)
	
	Args:
		funnel_name: Optional funnel name to edit (None for new workflow)
		
	Returns:
		{
			"success": bool,
			"builder_url": str,
			"message": str
		}
	"""
	if not is_nextai_installed():
		return {
			"success": False,
			"builder_url": None,
			"message": "NextAI not installed"
		}
	
	try:
		# NextAI's Funnel builder is at /app/funnel
		base_url = frappe.utils.get_url()
		
		if funnel_name:
			# Edit existing funnel
			funnel = frappe.get_doc("Funnel", funnel_name)
			builder_url = f"{base_url}/app/funnel/{funnel_name}"
		else:
			# Create new funnel
			builder_url = f"{base_url}/app/funnel/new-funnel-1"
		
		return {
			"success": True,
			"builder_url": builder_url,
			"message": "Builder URL generated"
		}
	except Exception as e:
		frappe.log_error(f"Builder URL error: {str(e)}")
		return {
			"success": False,
			"builder_url": None,
			"message": str(e)
		}


@frappe.whitelist()
def get_workflow_definition(funnel_name):
	"""
	Get workflow definition details
	
	Args:
		funnel_name: Name of Funnel Published
		
	Returns:
		Workflow definition with nodes and connections
	"""
	if not is_nextai_installed():
		frappe.throw("NextAI not installed")
	
	try:
		funnel = frappe.get_doc("Funnel Published", funnel_name)
		
		# Get all nodes
		nodes = frappe.get_all(
			"Funnel Definition",
			filters={"parent": funnel_name},
			fields=["id", "type", "element_type", "data", "position_x", "position_y"],
			order_by="idx asc"
		)
		
		return {
			"success": True,
			"funnel": funnel_name,
			"description": funnel.funnel_description,
			"nodes": nodes,
			"node_count": len(nodes)
		}
	except Exception as e:
		frappe.log_error(f"Workflow definition error: {str(e)}")
		return {
			"success": False,
			"error": str(e),
			"funnel": funnel_name,
			"nodes": [],
			"node_count": 0
		}

