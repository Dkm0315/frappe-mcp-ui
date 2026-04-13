"""
LLM Provider Configuration
Reads AI config from MCP Settings and returns litellm-compatible model strings.
Supports: Ollama, OpenAI, Anthropic, Google, Custom.
"""

import frappe

from mcp_ui.utils.app_checker import get_anthropic_api_key, get_openai_api_key


def get_provider_config() -> dict:
	"""
	Read AI chat configuration from MCP Settings.

	Returns:
		dict with keys: model, api_key, api_base, max_steps, enabled
	"""
	settings = frappe.get_single("MCP Settings")

	if not settings.ai_chat_enabled:
		return {"enabled": False}

	provider = settings.ai_provider or "OpenAI"
	configured_provider = provider
	model = None
	api_key = None
	api_base = None

	if provider == "Ollama":
		base_url = settings.ai_chat_base_url or "http://localhost:11434"
		model_name = settings.ai_chat_model or "qwen3:8b"
		# litellm format: ollama_chat/ prefix needed for tool calling support
		model = f"ollama_chat/{model_name}"
		api_base = base_url

	elif provider == "OpenAI":
		api_key = get_openai_api_key()
		model_name = settings.openai_model or "gpt-4o-mini"
		model = model_name

	elif provider == "Anthropic":
		api_key = get_anthropic_api_key()
		model_name = settings.anthropic_model or "claude-sonnet-4-6"
		model = model_name

	elif provider == "Google":
		api_key = _get_settings_secret(settings, "ai_chat_api_key")
		model_name = settings.ai_chat_model or "gemini-2.0-flash"
		model = f"gemini/{model_name}"

	else:
		# Custom provider — use ai_chat_model and ai_chat_base_url directly
		model = settings.ai_chat_model
		api_key = _get_settings_secret(settings, "ai_chat_api_key")
		api_base = settings.ai_chat_base_url

	if _should_fallback_to_ollama(provider, api_key):
		provider = "Ollama"
		api_key = "ollama-local"
		api_base = settings.ai_chat_base_url or "http://localhost:11434"
		model_name = settings.ai_chat_model or "qwen3:8b"
		model = f"ollama_chat/{model_name}"

	max_steps = settings.ai_chat_max_steps or 25

	return {
		"enabled": True,
		"provider": provider,
		"configured_provider": configured_provider,
		"model": model,
		"api_key": api_key,
		"api_base": api_base,
		"max_steps": int(max_steps),
		"using_fallback": provider == "Ollama" and configured_provider != "Ollama",
	}


def _get_settings_secret(settings, fieldname: str) -> str | None:
	try:
		value = settings.get_password(fieldname)
		if value and value.strip():
			return value
	except Exception:
		pass

	value = settings.get(fieldname)
	if isinstance(value, str):
		value = value.strip()
		if value and set(value) != {"*"}:
			return value
	return None


def _should_fallback_to_ollama(provider: str, api_key: str | None) -> bool:
	if provider == "Ollama":
		return False
	if api_key:
		return False
	return provider in {"OpenAI", "Anthropic", "Google", "Custom"} or bool(provider)


def get_allowed_doctypes() -> dict:
	"""
	Get the list of DocTypes the AI is allowed to access,
	with their CRUD permissions.

	Returns:
		dict mapping doctype_name -> {read, create, update, delete}
	"""
	try:
		settings = frappe.get_single("MCP Settings")
		allowed = {}
		for row in settings.get("ai_allowed_doctypes", []):
			allowed[row.doctype_name] = {
				"read": bool(row.allow_read),
				"create": bool(row.allow_create),
				"update": bool(row.allow_update),
				"delete": bool(row.allow_delete),
			}
		return allowed
	except Exception:
		return {}


def check_ai_access(doctype: str, operation: str = "read") -> bool:
	"""
	Check if the AI is allowed to perform an operation on a DocType.

	Args:
		doctype: The DocType name
		operation: 'read', 'create', 'update', or 'delete'

	Returns:
		True if allowed, False if not
	"""
	allowed = get_allowed_doctypes()

	# If no allowed doctypes configured, allow all (open access mode)
	if not allowed:
		return True

	if doctype not in allowed:
		return False

	return allowed[doctype].get(operation, False)


def get_system_prompt() -> str:
	"""
	Build the system prompt with Frappe context.

	Returns:
		Complete system prompt string
	"""
	settings = frappe.get_single("MCP Settings")

	# Use custom prompt if set
	if settings.ai_chat_system_prompt:
		return settings.ai_chat_system_prompt

	# Build context
	user = frappe.session.user
	user_doc = frappe.get_doc("User", user)
	user_name = user_doc.full_name or user
	user_roles = [r.role for r in user_doc.roles]
	installed_apps = frappe.get_installed_apps()

	# Get company name
	try:
		company = frappe.db.get_single_value("Global Defaults", "default_company") or "Your Company"
	except Exception:
		company = "Your Company"

	# Get allowed doctypes list
	allowed = get_allowed_doctypes()
	if allowed:
		doctype_list = ", ".join(sorted(allowed.keys()))
	else:
		doctype_list = "All DocTypes (open access mode)"

	return f"""You are a business automation engine for {company}'s Frappe/ERPNext system.
You don't just answer questions — you EXECUTE business processes end-to-end.

YOUR CAPABILITIES:
- Run full business process chains: Quotation → SO → DN → SI (use make_mapped_document to chain)
- Import Excel spreadsheets with hundreds of rows into any DocType
- Run and analyze reports, spotting trends and anomalies
- Bulk create/update/delete thousands of records
- Submit, cancel, and amend documents with workflow awareness
- Track document chains and linked documents across modules

BUSINESS PROCESS RULES:
- Before creating downstream docs, ALWAYS use get_document on the upstream doc to verify it exists and is Submitted
- Use make_mapped_document (NOT create_document) for SO→DN, DN→SI, PO→PR chains — it auto-maps all fields
- Before bulk operations, confirm the count with the user
- If a DocType has a workflow, use get_workflow_info to understand the approval chain
- For Excel imports, first use parse_excel to preview data, then import_from_excel
- When analyzing reports, run_report first, then provide your analysis inline

SECURITY RULES (NEVER VIOLATE):
- Never reveal another user's salary, compensation, or personal financial data
- Never share bank account details, passwords, or API keys
- Always confirm before deleting or modifying > 10 records
- If a permission error occurs, say "You don't have access to this data" — never reveal what the data contains
- Log all data access for audit purposes

Available DocTypes: {doctype_list}
Current user: {user_name} (Roles: {', '.join(user_roles)})
Installed apps: {', '.join(installed_apps)}"""
