"""
Bulk Operations API
Handles bulk document creation with AI-powered generation or standard batch processing
"""
import frappe
import json
from typing import List, Dict, Any
from mcp_ui.utils.app_checker import get_openai_api_key


@frappe.whitelist()
def bulk_create_documents(doctype, records=None, use_ai_generation=False, ai_template=None):
	"""
	Bulk create documents with two modes:
	1. Standard: User provides array of records
	2. AI-powered: Generate variations with OpenAI
	
	Args:
		doctype: DocType name
		records: JSON string of records array (for standard mode)
		use_ai_generation: Boolean flag for AI mode
		ai_template: JSON string with generation config (count, type, edge_cases)
		
	Returns:
		{
			"success": bool,
			"created": int,
			"failed": int,
			"created_names": list,
			"errors": list
		}
	"""
	# Check permissions
	if not frappe.has_permission(doctype, "create"):
		frappe.throw(f"No permission to create {doctype}")
	
	if use_ai_generation:
		if not ai_template:
			frappe.throw("AI template required for AI generation mode")
		template = json.loads(ai_template) if isinstance(ai_template, str) else ai_template
		return ai_generate_and_create(doctype, template)
	else:
		if not records:
			frappe.throw("Records required for standard bulk creation")
		records_list = json.loads(records) if isinstance(records, str) else records
		return standard_bulk_create(doctype, records_list)


def ai_generate_and_create(doctype: str, template: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Use OpenAI to generate realistic document variations
	
	Args:
		doctype: DocType name
		template: {
			"count": int,  # Number of records to generate
			"type": str,   # "mix", "companies", "individuals", etc.
			"edge_cases": bool,  # Include edge cases
			"base_data": dict  # Optional base values to use
		}
		
	Returns:
		{
			"success": bool,
			"created": int,
			"failed": int,
			"created_names": list,
			"errors": list,
			"mode": "ai_generated"
		}
	"""
	from openai import OpenAI
	
	api_key = get_openai_api_key()
	if not api_key:
		frappe.throw("OpenAI API key not configured in MCP Settings or ChatNext Settings")
	
	try:
		client = OpenAI(api_key=api_key)
		meta = frappe.get_meta(doctype)
		
		# Build schema for AI
		schema = build_doctype_schema(meta)
		
		# Extract template parameters
		count = template.get('count', 10)
		data_type = template.get('type', 'mix')
		edge_cases = template.get('edge_cases', True)
		base_data = template.get('base_data', {})
		
		# Build prompt
		edge_case_instruction = ""
		if edge_cases:
			edge_case_instruction = """
- Include edge cases (30% of records):
  * Missing optional fields
  * Special characters in text fields
  * Maximum and minimum values
  * Empty strings where allowed
  * Different date formats
  * Various phone/email formats
"""
		
		prompt = f"""Generate {count} realistic {doctype} records for testing an ERP system.

DocType Schema:
{json.dumps(schema, indent=2)}

Requirements:
- Generate {count} records total
- Type preference: {data_type}
- 70% normal realistic data
{edge_case_instruction}
- Use realistic names, addresses, phone numbers, emails
- Ensure data follows field validations
- Return ONLY valid JSON in this exact format: {{"records": [...]}}

Base data to incorporate:
{json.dumps(base_data, indent=2) if base_data else "None"}

Generate varied, realistic data suitable for testing."""
		
		# Call OpenAI
		response = client.chat.completions.create(
			model="gpt-4o-mini",
			messages=[
				{"role": "system", "content": "You are an ERP test data generator. Generate realistic, varied test data."},
				{"role": "user", "content": prompt}
			],
			response_format={"type": "json_object"},
			temperature=0.8  # Higher temperature for more variety
		)
		
		# Parse response
		generated_data = json.loads(response.choices[0].message.content)
		variations = generated_data.get('records', [])
		
		if not variations:
			frappe.throw("AI did not generate any records")
		
		# Create in bulk
		created = []
		failed = []
		
		for idx, data in enumerate(variations):
			try:
				# Merge with base data
				final_data = {**base_data, **data, "doctype": doctype}
				
				doc = frappe.get_doc(final_data)
				doc.insert(ignore_permissions=False)
				created.append(doc.name)
			except Exception as e:
				failed.append({
					"index": idx,
					"data": data,
					"error": str(e)
				})
		
		frappe.db.commit()
		
		return {
			"success": True,
			"created": len(created),
			"failed": len(failed),
			"created_names": created,
			"errors": failed,
			"mode": "ai_generated",
			"ai_model": "gpt-4o-mini"
		}
		
	except Exception as e:
		frappe.log_error(f"AI generation error: {str(e)}")
		frappe.throw(f"Failed to generate records: {str(e)}")


def standard_bulk_create(doctype: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
	"""
	Standard bulk document creation
	
	Args:
		doctype: DocType name
		records: List of record dicts
		
	Returns:
		{
			"success": bool,
			"created": int,
			"failed": int,
			"created_names": list,
			"errors": list,
			"mode": "standard"
		}
	"""
	created = []
	failed = []
	
	for idx, record in enumerate(records):
		try:
			doc_data = {**record, "doctype": doctype}
			doc = frappe.get_doc(doc_data)
			doc.insert(ignore_permissions=False)
			created.append(doc.name)
		except Exception as e:
			failed.append({
				"index": idx,
				"record": record,
				"error": str(e)
			})
	
	frappe.db.commit()
	
	return {
		"success": True,
		"created": len(created),
		"failed": len(failed),
		"created_names": created,
		"errors": failed,
		"mode": "standard"
	}


def build_doctype_schema(meta) -> Dict[str, Any]:
	"""
	Build a JSON schema from DocType metadata for AI
	
	Args:
		meta: DocType meta object
		
	Returns:
		Schema dict with fields and validations
	"""
	schema = {
		"doctype": meta.name,
		"fields": []
	}
	
	for field in meta.fields:
		# Skip system fields and layout fields
		if field.fieldtype in ['Section Break', 'Column Break', 'Tab Break', 'HTML', 'Button', 'Heading']:
			continue
		
		# Skip table fields for now (child tables)
		if field.fieldtype == 'Table':
			continue
		
		field_schema = {
			"fieldname": field.fieldname,
			"label": field.label or field.fieldname,
			"type": field.fieldtype,
			"required": bool(field.reqd),
		}
		
		# Add options for Select/Link fields
		if field.options:
			field_schema["options"] = field.options
		
		# Add description
		if field.description:
			field_schema["description"] = field.description
		
		# Add default value
		if field.default:
			field_schema["default"] = field.default
		
		schema["fields"].append(field_schema)
	
	return schema


@frappe.whitelist()
def bulk_update_documents(doctype, filters, update_data):
	"""
	Bulk update documents matching filters
	
	Args:
		doctype: DocType name
		filters: JSON string of filters
		update_data: JSON string of fields to update
		
	Returns:
		{
			"success": bool,
			"updated": int,
			"failed": int,
			"errors": list
		}
	"""
	# Check permissions
	if not frappe.has_permission(doctype, "write"):
		frappe.throw(f"No permission to update {doctype}")
	
	try:
		filters_dict = json.loads(filters) if isinstance(filters, str) else filters
		update_dict = json.loads(update_data) if isinstance(update_data, str) else update_data
		
		# Get matching documents
		docs = frappe.get_all(doctype, filters=filters_dict, pluck="name")
		
		updated = []
		failed = []
		
		for doc_name in docs:
			try:
				doc = frappe.get_doc(doctype, doc_name)
				for key, value in update_dict.items():
					if hasattr(doc, key):
						setattr(doc, key, value)
				doc.save(ignore_permissions=False)
				updated.append(doc_name)
			except Exception as e:
				failed.append({
					"name": doc_name,
					"error": str(e)
				})
		
		frappe.db.commit()
		
		return {
			"success": True,
			"updated": len(updated),
			"failed": len(failed),
			"errors": failed
		}
		
	except Exception as e:
		frappe.log_error(f"Bulk update error: {str(e)}")
		frappe.throw(f"Bulk update failed: {str(e)}")


@frappe.whitelist()
def bulk_delete_documents(doctype, filters):
	"""
	Bulk delete documents matching filters
	
	Args:
		doctype: DocType name
		filters: JSON string of filters
		
	Returns:
		{
			"success": bool,
			"deleted": int,
			"failed": int,
			"errors": list
		}
	"""
	# Check permissions
	if not frappe.has_permission(doctype, "delete"):
		frappe.throw(f"No permission to delete {doctype}")
	
	try:
		filters_dict = json.loads(filters) if isinstance(filters, str) else filters
		
		# Get matching documents
		docs = frappe.get_all(doctype, filters=filters_dict, pluck="name")
		
		deleted = []
		failed = []
		
		for doc_name in docs:
			try:
				frappe.delete_doc(doctype, doc_name, ignore_permissions=False)
				deleted.append(doc_name)
			except Exception as e:
				failed.append({
					"name": doc_name,
					"error": str(e)
				})
		
		frappe.db.commit()
		
		return {
			"success": True,
			"deleted": len(deleted),
			"failed": len(failed),
			"errors": failed
		}
		
	except Exception as e:
		frappe.log_error(f"Bulk delete error: {str(e)}")
		frappe.throw(f"Bulk delete failed: {str(e)}")
