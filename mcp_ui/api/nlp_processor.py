"""
Natural Language Processing
Converts simple English commands to tool executions
"""
import re
import frappe


@frappe.whitelist()
def parse_natural_language(query):
	"""
	Parse natural language query and suggest tool + parameters
	
	Args:
		query: User's natural language query
		
	Returns:
		Suggested tool and pre-filled parameters
	"""
	query = query.lower().strip()
	
	suggestions = []
	
	# Pattern: Create/Add/New + DocType
	create_patterns = [
		r"(?:create|add|new)\s+(?:a\s+)?(\w+)",
		r"(?:i\s+want\s+to\s+create|i\s+need\s+to\s+add)\s+(?:a\s+)?(\w+)",
	]
	
	for pattern in create_patterns:
		match = re.search(pattern, query)
		if match:
			entity = match.group(1).title()
			# Try to find matching DocType
			doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")
			
			for dt in doctypes:
				if entity.lower() in dt.lower():
					suggestions.append({
						"confidence": "high",
						"tool": "create_document",
						"params": {"doctype": dt},
						"description": f"Create a new {dt}",
						"next_step": "form"
					})
	
	# Pattern: Get/Show/List + DocType
	list_patterns = [
		r"(?:show|get|list|find)\s+(?:all\s+)?(\w+)",
		r"(?:i\s+want\s+to\s+see|show\s+me)\s+(?:all\s+)?(\w+)",
	]
	
	for pattern in list_patterns:
		match = re.search(pattern, query)
		if match:
			entity = match.group(1).title()
			doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")
			
			for dt in doctypes:
				if entity.lower() in dt.lower():
					suggestions.append({
						"confidence": "high",
						"tool": "get_list",
						"params": {"doctype": dt, "limit": 20},
						"description": f"List all {dt}s",
						"next_step": "execute"
					})
	
	# Pattern: Search + text + in + DocType
	search_pattern = r"search\s+(?:for\s+)?['\"]?([^'\"]+)['\"]?\s+in\s+(\w+)"
	match = re.search(search_pattern, query)
	if match:
		search_text = match.group(1)
		entity = match.group(2).title()
		
		doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")
		for dt in doctypes:
			if entity.lower() in dt.lower():
				suggestions.append({
					"confidence": "high",
					"tool": "search_documents",
					"params": {"doctype": dt, "search_text": search_text},
					"description": f"Search for '{search_text}' in {dt}",
					"next_step": "execute"
				})
	
	# Pattern: Update/Modify/Change
	update_pattern = r"(?:update|modify|change|edit)\s+(\w+)\s+(?:named\s+)?['\"]?([^'\"]+)['\"]?"
	match = re.search(update_pattern, query)
	if match:
		entity = match.group(1).title()
		name = match.group(2)
		
		doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")
		for dt in doctypes:
			if entity.lower() in dt.lower():
				suggestions.append({
					"confidence": "medium",
					"tool": "update_document",
					"params": {"doctype": dt, "name": name},
					"description": f"Update {dt}: {name}",
					"next_step": "form"
				})
	
	# Pattern: Delete/Remove
	delete_pattern = r"(?:delete|remove)\s+(\w+)\s+(?:named\s+)?['\"]?([^'\"]+)['\"]?"
	match = re.search(delete_pattern, query)
	if match:
		entity = match.group(1).title()
		name = match.group(2)
		
		doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")
		for dt in doctypes:
			if entity.lower() in dt.lower():
				suggestions.append({
					"confidence": "high",
					"tool": "delete_document",
					"params": {"doctype": dt, "name": name},
					"description": f"Delete {dt}: {name}",
					"next_step": "confirm",
					"warning": "This is a destructive operation"
				})
	
	# Pattern: Dashboard/Statistics
	if any(word in query for word in ["dashboard", "statistics", "stats", "overview"]):
		entity_match = re.search(r"(?:for|of)\s+(\w+)", query)
		if entity_match:
			entity = entity_match.group(1).title()
			doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")
			
			for dt in doctypes:
				if entity.lower() in dt.lower():
					suggestions.append({
						"confidence": "high",
						"tool": "get_dashboard_data",
						"params": {"doctype": dt},
						"description": f"Show dashboard for {dt}",
						"next_step": "execute"
					})
	
	if not suggestions:
		# Provide helpful suggestions
		suggestions.append({
			"confidence": "low",
			"message": "I didn't understand that. Try:",
			"examples": [
				"Create a new customer",
				"Show all items",
				"Search for John in customers",
				"Get dashboard for sales orders"
			]
		})
	
	return {
		"success": True,
		"query": query,
		"suggestions": suggestions
	}

