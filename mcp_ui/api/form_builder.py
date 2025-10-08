"""
Form Builder API
Converts DocTypes into user-friendly form schemas
"""
import frappe


@frappe.whitelist()
def get_doctype_form_fields(doctype):
	"""
	Get form fields for a DocType in a user-friendly format
	
	Args:
		doctype: DocType name
		
	Returns:
		List of field configurations for form building
	"""
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(f"DocType '{doctype}' not found")
	
	meta = frappe.get_meta(doctype)
	
	form_fields = []
	
	for field in meta.fields:
		# Skip internal fields
		if field.fieldtype in ["Section Break", "Column Break", "Tab Break", "HTML", "Table", "Attach Image"]:
			continue
			
		if field.hidden or field.read_only:
			continue
		
		field_config = {
			"fieldname": field.fieldname,
			"label": field.label or field.fieldname.replace("_", " ").title(),
			"fieldtype": field.fieldtype,
			"required": field.reqd,
			"description": field.description,
			"default": field.default,
		}
		
		# Handle different field types
		if field.fieldtype == "Link":
			field_config["link_doctype"] = field.options
			field_config["input_type"] = "autocomplete"
			
		elif field.fieldtype == "Select":
			if field.options:
				field_config["options"] = [opt.strip() for opt in field.options.split("\n") if opt.strip()]
			field_config["input_type"] = "select"
			
		elif field.fieldtype in ["Int", "Long Int"]:
			field_config["input_type"] = "number"
			field_config["number_type"] = "integer"
			
		elif field.fieldtype in ["Float", "Currency", "Percent"]:
			field_config["input_type"] = "number"
			field_config["number_type"] = "decimal"
			
		elif field.fieldtype == "Check":
			field_config["input_type"] = "checkbox"
			
		elif field.fieldtype == "Date":
			field_config["input_type"] = "date"
			
		elif field.fieldtype == "Datetime":
			field_config["input_type"] = "datetime"
			
		elif field.fieldtype == "Time":
			field_config["input_type"] = "time"
			
		elif field.fieldtype in ["Small Text", "Text", "Long Text"]:
			field_config["input_type"] = "textarea"
			
		elif field.fieldtype == "Text Editor":
			field_config["input_type"] = "richtext"
			
		else:
			field_config["input_type"] = "text"
		
		form_fields.append(field_config)
	
	return {
		"success": True,
		"doctype": doctype,
		"title_field": meta.title_field,
		"fields": form_fields,
	}


@frappe.whitelist()
def search_link_field(doctype, search_term, limit=20):
	"""
	Search for link field values (autocomplete)
	
	Args:
		doctype: DocType to search
		search_term: Search query
		limit: Max results
		
	Returns:
		List of matching documents
	"""
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(f"DocType '{doctype}' not found")
	
	meta = frappe.get_meta(doctype)
	
	# Build search fields
	search_fields = ["name"]
	if meta.title_field:
		search_fields.append(meta.title_field)
	if meta.search_fields:
		search_fields.extend(meta.search_fields.split(","))
	
	# Remove duplicates and clean
	search_fields = list(set([f.strip() for f in search_fields]))
	
	# Build filters
	or_filters = []
	for field in search_fields[:3]:  # Limit to 3 fields
		or_filters.append([doctype, field, "like", f"%{search_term}%"])
	
	results = frappe.get_all(
		doctype,
		or_filters=or_filters,
		fields=search_fields,
		limit=int(limit)
	)
	
	# Format results
	formatted = []
	for doc in results:
		label = doc.get(meta.title_field) or doc.get("name")
		formatted.append({
			"value": doc.get("name"),
			"label": label,
			"description": " • ".join([str(v) for k, v in doc.items() if k != "name" and v])
		})
	
	return formatted


@frappe.whitelist()
def get_quick_create_templates():
	"""
	Get pre-configured templates for common operations
	"""
	templates = {
		"Customer": {
			"icon": "👤",
			"title": "Create Customer",
			"description": "Add a new customer to the system",
			"fields": ["customer_name", "customer_type", "customer_group", "territory", "mobile_no", "email_id"]
		},
		"Supplier": {
			"icon": "🏢",
			"title": "Create Supplier",
			"description": "Add a new supplier",
			"fields": ["supplier_name", "supplier_group", "supplier_type", "mobile_no", "email_id"]
		},
		"Item": {
			"icon": "📦",
			"title": "Create Item",
			"description": "Add a new product or service",
			"fields": ["item_code", "item_name", "item_group", "stock_uom", "standard_rate", "description"]
		},
		"Lead": {
			"icon": "🎯",
			"title": "Create Lead",
			"description": "Add a new sales lead",
			"fields": ["lead_name", "company_name", "email_id", "mobile_no", "source", "status"]
		},
		"Task": {
			"icon": "✅",
			"title": "Create Task",
			"description": "Create a new task",
			"fields": ["subject", "project", "status", "priority", "expected_time", "description"]
		},
		"ToDo": {
			"icon": "📝",
			"title": "Create To-Do",
			"description": "Add a to-do item",
			"fields": ["description", "priority", "status", "date"]
		},
	}
	
	available_templates = []
	
	for doctype, template in templates.items():
		if frappe.db.exists("DocType", doctype):
			available_templates.append({
				"doctype": doctype,
				**template
			})
	
	return {
		"success": True,
		"templates": available_templates
	}

