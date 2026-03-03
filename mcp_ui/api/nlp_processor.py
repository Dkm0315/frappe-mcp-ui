"""
Natural Language Processing
Converts simple English commands to tool executions
"""
import re
import frappe


# Words to skip when extracting entity names from queries
STOP_WORDS = {"a", "an", "the", "new", "some", "my", "all", "any", "this", "that", "one"}


def singularize(word):
	"""Basic English singularization for common plural forms"""
	w = word.lower()
	if w.endswith("ies"):
		return w[:-3] + "y"
	if w.endswith("ses") or w.endswith("xes") or w.endswith("zes") or w.endswith("ches") or w.endswith("shes"):
		return w[:-2]
	if w.endswith("s") and not w.endswith("ss"):
		return w[:-1]
	return w


def find_best_doctype(entity, doctypes):
	"""
	Find the best matching DocType for an entity string.
	Uses scored matching: exact > starts-with > word-in-name > substring.
	Returns (doctype_name, score) or (None, 0).
	"""
	entity_lower = entity.lower()
	singular = singularize(entity_lower)

	best = None
	best_score = 0

	for dt in doctypes:
		dt_lower = dt.lower()
		dt_words = dt_lower.replace("_", " ").split()

		# Exact match (singular or original)
		if entity_lower == dt_lower or singular == dt_lower:
			return dt, 100

		# First word match (e.g., "customer" matches "Customer Group")
		if dt_words and (dt_words[0] == entity_lower or dt_words[0] == singular):
			if best_score < 80:
				best = dt
				best_score = 80

		# Starts-with match
		elif dt_lower.startswith(entity_lower) or dt_lower.startswith(singular):
			if best_score < 60:
				best = dt
				best_score = 60

		# Word appears in DocType name
		elif entity_lower in dt_words or singular in dt_words:
			if best_score < 40:
				best = dt
				best_score = 40

	return best, best_score


def extract_entity(text):
	"""Extract the meaningful entity from text, skipping stop words."""
	words = text.strip().split()
	# Filter out stop words and return remaining words joined
	meaningful = [w for w in words if w.lower() not in STOP_WORDS]
	return " ".join(meaningful) if meaningful else text


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

	# Cache DocType list (used across patterns)
	doctypes = frappe.get_all("DocType", filters={"istable": 0}, pluck="name")

	# Pattern: Create/Add/New + DocType
	create_patterns = [
		r"(?:create|add|make)\s+([\w\s]+?)(?:\s+document|\s+record|\s+entry)?$",
		r"(?:i\s+want\s+to\s+create|i\s+need\s+to\s+add)\s+([\w\s]+?)(?:\s+document|\s+record|\s+entry)?$",
		r"new\s+([\w\s]+?)(?:\s+document|\s+record|\s+entry)?$",
	]

	for pattern in create_patterns:
		match = re.search(pattern, query)
		if match:
			raw = match.group(1)
			entity = extract_entity(raw).title()
			if not entity:
				continue

			dt, score = find_best_doctype(entity, doctypes)
			if dt and score >= 40:
				suggestions.append({
					"confidence": "high",
					"tool": "create_document",
					"params": {"doctype": dt},
					"description": f"Create a new {dt}",
					"next_step": "form"
				})
				break

	# Pattern: Get/Show/List + DocType
	if not suggestions:
		list_patterns = [
			r"(?:show|get|list|find|display|view)\s+([\w\s]+?)$",
			r"(?:i\s+want\s+to\s+see|show\s+me)\s+([\w\s]+?)$",
		]

		for pattern in list_patterns:
			match = re.search(pattern, query)
			if match:
				raw = match.group(1)
				entity = extract_entity(raw).title()
				if not entity:
					continue

				dt, score = find_best_doctype(entity, doctypes)
				if dt and score >= 40:
					suggestions.append({
						"confidence": "high",
						"tool": "get_list",
						"params": {"doctype": dt, "limit": 20},
						"description": f"List all {dt}s",
						"next_step": "execute"
					})
					break

	# Pattern: Search + text + in + DocType
	if not suggestions:
		search_pattern = r"search\s+(?:for\s+)?['\"]?([^'\"]+?)['\"]?\s+in\s+([\w\s]+?)$"
		match = re.search(search_pattern, query)
		if match:
			search_text = match.group(1).strip()
			entity = extract_entity(match.group(2)).title()

			dt, score = find_best_doctype(entity, doctypes)
			if dt and score >= 40:
				suggestions.append({
					"confidence": "high",
					"tool": "search_documents",
					"params": {"doctype": dt, "search_text": search_text},
					"description": f"Search for '{search_text}' in {dt}",
					"next_step": "execute"
				})

	# Pattern: Update/Modify/Change
	if not suggestions:
		update_pattern = r"(?:update|modify|change|edit)\s+([\w\s]+?)\s+(?:named\s+)?['\"]?([^'\"]+)['\"]?$"
		match = re.search(update_pattern, query)
		if match:
			entity = extract_entity(match.group(1)).title()
			name = match.group(2).strip()

			dt, score = find_best_doctype(entity, doctypes)
			if dt and score >= 40:
				suggestions.append({
					"confidence": "medium",
					"tool": "update_document",
					"params": {"doctype": dt, "name": name},
					"description": f"Update {dt}: {name}",
					"next_step": "form"
				})

	# Pattern: Delete/Remove
	if not suggestions:
		delete_pattern = r"(?:delete|remove)\s+([\w\s]+?)\s+(?:named\s+)?['\"]?([^'\"]+)['\"]?$"
		match = re.search(delete_pattern, query)
		if match:
			entity = extract_entity(match.group(1)).title()
			name = match.group(2).strip()

			dt, score = find_best_doctype(entity, doctypes)
			if dt and score >= 40:
				suggestions.append({
					"confidence": "high",
					"tool": "delete_document",
					"params": {"doctype": dt, "name": name},
					"description": f"Delete {dt}: {name}",
					"next_step": "confirm",
					"warning": "This is a destructive operation"
				})

	# Pattern: Dashboard/Statistics
	if not suggestions:
		if any(word in query for word in ["dashboard", "statistics", "stats", "overview"]):
			entity_match = re.search(r"(?:for|of)\s+([\w\s]+?)$", query)
			if entity_match:
				entity = extract_entity(entity_match.group(1)).title()

				dt, score = find_best_doctype(entity, doctypes)
				if dt and score >= 40:
					suggestions.append({
						"confidence": "high",
						"tool": "get_dashboard_data",
						"params": {"doctype": dt},
						"description": f"Show dashboard for {dt}",
						"next_step": "execute"
					})

	if not suggestions:
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
