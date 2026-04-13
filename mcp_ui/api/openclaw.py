"""
OpenClaw Configuration API
Generates openclaw.json, manages Telegram user mappings, health checks.
"""
import json
import os

import frappe
from frappe.utils import cint

from mcp_ui.ai.providers import get_provider_config
from mcp_ui.openclaw.federation import (
	execute_as_mapped_user,
	get_action_catalog_payload,
	get_session_mode_payload,
	plan_request_with_context_payload,
	retrieve_site_context_payload,
	resolve_identity_record,
	set_session_mode_payload,
)
from mcp_ui.openclaw.runtime import ensure_runtime_dirs
from mcp_ui.openclaw.site_context import (
	get_change_summary as get_change_summary_payload,
	get_site_manifest as get_site_manifest_payload,
	search_site_context as search_site_context_payload,
	refresh_site_context,
)


@frappe.whitelist()
def generate_config():
	"""Generate a bench-local OpenClaw config rooted inside the current site."""
	import secrets

	settings = frappe.get_single("MCP Settings")
	provider_config = get_provider_config()
	paths = ensure_runtime_dirs(frappe.local.site)
	bench_path = paths["bench_path"]
	python_path = os.path.join(bench_path, "env", "bin", "python")
	site = paths["site"]
	plugin_path = paths["app_plugin_dir"]

	# Build model string for OpenClaw
	model = _get_openclaw_model(settings, provider_config)
	provider = provider_config.get("provider") or settings.ai_provider or "OpenAI"

	shared_skill_dirs = []
	candidate_shared_skills = [
		os.path.join(bench_path, "apps", "openclaw_skills", "skills"),
		os.path.join(bench_path, "apps", "mcp_ui", "openclaw_skills", "skills"),
	]
	for candidate in candidate_shared_skills:
		if os.path.isdir(candidate):
			shared_skill_dirs.append(candidate)

	config = {
		"agents": {
			"defaults": {
				"model": model,
				"compaction": {"mode": "safeguard"},
				"contextInjection": "continuation-skip",
				"bootstrapMaxChars": 2500,
				"bootstrapTotalMaxChars": 5000,
				"bootstrapPromptTruncationWarning": "off",
				"thinkingDefault": "off",
			},
		},
		"commands": {
			"native": "auto",
			"nativeSkills": False,
			"restart": True,
			"ownerDisplay": "raw",
		},
		"models": {
			"providers": _build_model_provider_config(settings, provider_config),
		},
		"skills": {
			"load": {
				"extraDirs": shared_skill_dirs,
				"watch": True,
			},
		},
		"channels": {},
		"gateway": {
			"mode": "local",
			"auth": {
				"mode": "token",
				"token": secrets.token_hex(24),
			},
		},
		"browser": {
			"enabled": bool(settings.get("browser_enabled")),
			"evaluateEnabled": True,
			"defaultProfile": settings.get("browser_default_profile") or "openclaw",
			"headless": bool(settings.get("browser_headless")),
			"ssrfPolicy": {
				"allowedHostnames": _get_allowed_browser_hosts(site),
			},
			"profiles": {
				"openclaw": {
					"cdpPort": 18800,
					"color": "#FF4500",
				},
				"user": {
					"driver": "existing-session",
					"attachOnly": True,
					"color": "#00AA00",
				},
			},
			"color": "#FF4500",
		},
		"plugins": {
			"load": {
				"paths": [plugin_path],
			},
			"entries": {
				"frappe-federated": {
					"enabled": True,
					"config": {
						"site": site,
						"benchPath": bench_path,
						"pythonPath": python_path,
						"bridgeModule": "mcp_ui.openclaw.plugin_bridge",
						"bootUser": os.environ.get("FRAPPE_BOOT_USER", "Administrator"),
					},
				},
			},
		},
	}

	if os.environ.get("OPENCLAW_INCLUDE_STDIO_FALLBACK") == "1":
		config["plugins"]["entries"]["openclaw-mcp-adapter"] = {
			"enabled": True,
			"config": {
				"toolPrefix": True,
				"servers": [
					{
						"name": "frappe",
						"transport": "stdio",
						"command": python_path,
						"args": ["-m", "mcp_ui.openclaw"],
						"env": {
							"FRAPPE_SITE": site,
							"FRAPPE_BENCH": bench_path,
						},
					}
				],
			},
		}

	telegram_token = _get_secret(settings, "telegram_bot_token")
	if telegram_token:
		telegram_usernames = sorted(
			{
				(row.external_username or "").strip().lstrip("@")
				for row in settings.get("identity_mappings", [])
				if (row.channel or "").lower() == "telegram" and row.enabled and (row.external_username or "").strip()
			}
		)
		config["channels"]["telegram"] = {
			"enabled": True,
			"botToken": telegram_token,
			"dmPolicy": "open",
			"allowFrom": ["*"],
			"groupPolicy": "allowlist",
			"textChunkLimit": 4000,
			"streaming": "partial",
		}
		if telegram_usernames:
			config["channels"]["telegram"]["notes"] = {
				"identityResolution": "OpenClaw DM auth is open; Frappe-side federation restricts actual access by Telegram username/email mapping.",
				"configuredTelegramUsernames": telegram_usernames,
			}

	browser_executable_path = (settings.get("browser_executable_path") or "").strip()
	if browser_executable_path:
		config["browser"]["executablePath"] = browser_executable_path

	config_path = paths["config_file"]
	with open(config_path, "w") as f:
		json.dump(config, f, indent=2)

	_write_model_auth_profiles(paths, settings, provider_config)

	refresh_result = refresh_site_context(site=site, reason="config_generation")
	soul_result = generate_soul_md()
	settings.db_set("openclaw_config_path", config_path, update_modified=False)
	settings.db_set("openclaw_runtime_root", paths["root"], update_modified=False)

	env_key = _get_env_key_name(provider)
	instructions = [
		f"Config saved to: {config_path}",
		f"Runtime root: {paths['root']}",
		f"Workspace: {paths['workspace']}",
		f"Generated skills: {len(refresh_result.get('skills', []))}",
		f"SOUL.md generated: {soul_result.get('path')}",
		"",
		"Setup steps:",
	]
	if provider == "Ollama":
		ollama_model = _extract_ollama_model_name(provider_config.get("model", "qwen3:8b"))
		instructions.append("1. Start Ollama: ollama serve")
		instructions.append(f"2. Pull model: ollama pull {ollama_model}")
		instructions.append("3. Start the gateway through MCP Settings or mcp_ui.openclaw.manager.")
	elif env_key:
		instructions.append(f"1. Set API key: export {env_key}='your-api-key'")
		instructions.append("2. Start the gateway through MCP Settings or mcp_ui.openclaw.manager.")
	else:
		instructions.append("1. Start the gateway through MCP Settings or mcp_ui.openclaw.manager.")

	safe_config = json.loads(json.dumps(config))
	if telegram_token:
		safe_config["channels"]["telegram"]["botToken"] = "***masked***"
	safe_config["gateway"]["auth"]["token"] = "***masked***"
	_mask_model_provider_secrets(safe_config)

	return {
		"success": True,
		"config_path": config_path,
		"runtime_root": paths["root"],
		"workspace": paths["workspace"],
		"config": safe_config,
		"refresh": refresh_result,
		"soul_md": soul_result,
		"instructions": instructions,
	}


@frappe.whitelist()
def test_mcp_server():
	"""Test that the MCP server can initialize and list tools."""
	try:
		from mcp_ui.ai.tools import get_tool_schemas
		schemas = get_tool_schemas()
		tool_names = [s["function"]["name"] for s in schemas]
		return {
			"success": True,
			"tool_count": len(tool_names),
			"tools": tool_names,
		}
	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_available_modules():
	"""Get all Frappe modules with their DocType counts."""
	modules = frappe.db.sql("""
		SELECT m.name, COUNT(d.name) as doctype_count
		FROM `tabModule Def` m
		LEFT JOIN `tabDocType` d ON d.module = m.name AND d.istable = 0
		GROUP BY m.name
		ORDER BY doctype_count DESC
	""", as_dict=True)

	return {
		"success": True,
		"modules": [
			{"name": m.name, "doctype_count": m.doctype_count}
			for m in modules if m.doctype_count > 0
		],
	}


@frappe.whitelist()
def get_telegram_user(telegram_username: str):
	"""Look up the mapped Frappe user for a Telegram identity."""
	return resolve_identity_record(channel="telegram", external_username=telegram_username)


@frappe.whitelist()
def resolve_identity(channel: str, external_id: str = "", external_username: str = "", site_hint: str = "", chat_id: str = "", thread_id: str = ""):
	return resolve_identity_record(
		channel=channel,
		external_id=external_id,
		external_username=external_username,
		site_hint=site_hint,
		chat_id=chat_id,
		thread_id=thread_id,
	)


@frappe.whitelist(methods=["POST"])
def execute_as_user(session_context=None, action: str = "", args=None, validate_only: int = 0):
	if frappe.request and frappe.request.method == "POST":
		try:
			payload = frappe.request.get_json(force=False, silent=True) or {}
		except Exception:
			payload = {}
		session_context = session_context if session_context is not None else payload.get("session_context")
		action = action or payload.get("action", "")
		args = args if args is not None else payload.get("args")
		validate_only = validate_only or payload.get("validate_only", 0)
		confirmed = payload.get("confirmed", 0)
		confirmation_note = payload.get("confirmation_note", "")
	else:
		confirmed = frappe.form_dict.get("confirmed", 0)
		confirmation_note = frappe.form_dict.get("confirmation_note", "")

	if session_context is None:
		session_context = frappe.form_dict.get("session_context") or {}
	if args is None:
		args = frappe.form_dict.get("args") or {}

	if isinstance(session_context, str):
		session_context = json.loads(session_context)
	if isinstance(args, str):
		args = json.loads(args)

	return execute_as_mapped_user(
		session_context=session_context or {},
		action=action,
		args=args or {},
		validate_only=bool(int(validate_only)),
		confirmed=bool(int(confirmed)) if isinstance(confirmed, (str, int)) else bool(confirmed),
		confirmation_note=confirmation_note or "",
	)


@frappe.whitelist()
def get_site_manifest(site: str = "", refresh: int = 0, detail_level: str = "summary", sections: str = "", limit_per_section: int = 10):
	parsed_sections = None
	if sections:
		parsed_sections = [section.strip() for section in sections.split(",") if section.strip()]
	return get_site_manifest_payload(
		site=site or None,
		refresh=bool(int(refresh)),
		detail_level=detail_level or "summary",
		sections=parsed_sections,
		limit_per_section=cint(limit_per_section) or 10,
	)


@frappe.whitelist()
def search_site_context(site: str = "", query: str = "", sections: str = "", limit: int = 12):
	parsed_sections = None
	if sections:
		parsed_sections = [section.strip() for section in sections.split(",") if section.strip()]
	return search_site_context_payload(
		site=site or None,
		query=query,
		sections=parsed_sections,
		limit=cint(limit) or 12,
	)


@frappe.whitelist()
def retrieve_site_context(site: str = "", query: str = "", limit: int = 5):
	return retrieve_site_context_payload(site=site or None, query=query, limit=cint(limit) or 5)


@frappe.whitelist(methods=["POST"])
def plan_request(session_context=None, request: str = "", draft=None):
	if frappe.request and frappe.request.method == "POST":
		try:
			payload = frappe.request.get_json(force=False, silent=True) or {}
		except Exception:
			payload = {}
		session_context = session_context if session_context is not None else payload.get("session_context")
		request = request or payload.get("request", "")
		draft = draft if draft is not None else payload.get("draft")

	session_context = session_context or {}
	draft = draft or {}
	if isinstance(session_context, str):
		session_context = json.loads(session_context)
	if isinstance(draft, str):
		draft = json.loads(draft)
	return plan_request_with_context_payload(session_context=session_context, request=request, draft=draft)


@frappe.whitelist(methods=["POST"])
def get_session_mode(session_context=None):
	if frappe.request and frappe.request.method == "POST":
		try:
			payload = frappe.request.get_json(force=False, silent=True) or {}
		except Exception:
			payload = {}
		session_context = session_context if session_context is not None else payload.get("session_context")
	session_context = session_context or {}
	if isinstance(session_context, str):
		session_context = json.loads(session_context)
	return get_session_mode_payload(session_context)


@frappe.whitelist(methods=["POST"])
def set_session_mode(session_context=None, mode: str = "normal"):
	if frappe.request and frappe.request.method == "POST":
		try:
			payload = frappe.request.get_json(force=False, silent=True) or {}
		except Exception:
			payload = {}
		session_context = session_context if session_context is not None else payload.get("session_context")
		mode = mode or payload.get("mode", "normal")
	session_context = session_context or {}
	if isinstance(session_context, str):
		session_context = json.loads(session_context)
	return set_session_mode_payload(session_context, mode=mode)


@frappe.whitelist()
def refresh_context(site: str = "", reason: str = "manual"):
	return refresh_site_context(site=site or None, reason=reason)


@frappe.whitelist()
def get_change_summary(site: str = "", since_hash_or_timestamp: str = ""):
	return get_change_summary_payload(site=site or None, since_hash_or_timestamp=since_hash_or_timestamp or None)


@frappe.whitelist()
def get_action_catalog(query: str = "", category: str = "", write_only: int = 0, destructive_only: int = 0, limit: int = 12, verbose: int = 0):
	return get_action_catalog_payload(
		query=query,
		category=category,
		write_only=bool(cint(write_only)),
		destructive_only=bool(cint(destructive_only)),
		limit=cint(limit) or 12,
		verbose=bool(cint(verbose)),
	)


@frappe.whitelist()
def get_openclaw_status():
	"""Health check: verify OpenClaw configuration is complete."""
	settings = frappe.get_single("MCP Settings")
	issues = []
	paths = ensure_runtime_dirs(frappe.local.site)

	if not settings.get("ai_chat_enabled"):
		issues.append("AI Chat is not enabled")
	if not settings.get("openclaw_enabled"):
		issues.append("OpenClaw is not enabled")
	if not settings.get("telegram_bot_token"):
		issues.append("Telegram Bot Token is not set")
	if not settings.get("identity_mappings") and not settings.get("telegram_user_mappings"):
		issues.append("No federated identity mappings configured")
	elif settings.get("telegram_bot_token"):
		has_telegram_username_identity = any(
			(row.channel or "").strip().lower() == "telegram"
			and row.enabled
			and ((row.external_username or "").strip() or (row.external_id or "").strip())
			for row in settings.get("identity_mappings", [])
		)
		if not has_telegram_username_identity:
			issues.append("Telegram requires at least one enabled username or sender mapping")

	try:
		manifest = get_site_manifest_payload()
		tool_count = get_action_catalog_payload().get("count", 0)
	except Exception as e:
		tool_count = 0
		issues.append(f"MCP tools failed to load: {str(e)}")
		manifest = {}

	from mcp_ui.ai.providers import get_provider_config
	provider_config = get_provider_config()
	effective_provider = provider_config.get("provider") or settings.ai_provider or "Not set"
	if not provider_config.get("model"):
		issues.append("No AI model configured")
	elif _provider_requires_api_key(effective_provider) and not provider_config.get("api_key"):
		issues.append(f"No API key configured for provider {effective_provider}")

	return {
		"success": len(issues) == 0,
		"tool_count": tool_count,
		"provider": effective_provider,
		"configured_provider": settings.ai_provider or "Not set",
		"model": provider_config.get("model", "Not set"),
		"using_provider_fallback": bool(provider_config.get("using_fallback")),
		"telegram_configured": bool(settings.get("telegram_bot_token")),
		"user_mappings": len(settings.get("identity_mappings", [])) + len(settings.get("telegram_user_mappings", [])),
		"browser_enabled": bool(settings.get("browser_enabled")),
		"browser_headless": bool(settings.get("browser_headless")),
		"browser_default_profile": settings.get("browser_default_profile") or "openclaw",
		"runtime_root": paths["root"],
		"config_path": paths["config_file"],
		"plugin_path": paths["app_plugin_dir"],
		"manifest_hash": manifest.get("manifest_hash"),
		"issues": issues,
	}


@frappe.whitelist()
def generate_soul_md():
	"""Generate SOUL.md dynamically from the live Frappe system.

	Discovers all DocTypes, groups by module, and writes to
	~/.openclaw/workspace/SOUL.md so the bot always knows correct names.
	"""
	import os

	# Get company name
	try:
		company = frappe.db.get_single_value("Global Defaults", "default_company") or "Your Company"
	except Exception:
		company = "Your Company"

	# Get all non-table DocTypes grouped by module
	doctypes = frappe.get_all(
		"DocType",
		filters={"istable": 0, "custom": 0},
		fields=["name", "module"],
		order_by="module, name",
		limit=500,
	)

	# Group by module
	modules = {}
	for dt in doctypes:
		mod = dt.module
		if mod not in modules:
			modules[mod] = []
		modules[mod].append(dt.name)

	# Build a concise module reference section from the live system instead of a fixed preference list.
	dt_lines = []
	module_counts = sorted(((mod, len(names)) for mod, names in modules.items() if names), key=lambda item: (-item[1], item[0]))
	for mod, _count in module_counts[:10]:
		names = ", ".join(f'"{n}"' for n in modules[mod][:3])
		dt_lines.append(f"- **{mod}**: {len(modules[mod])} doctypes, examples: {names}")

	module_ref = "\n".join(dt_lines)

	# Get installed apps
	installed_apps = ", ".join(frappe.get_installed_apps())

	# Get current user info
	user = frappe.session.user
	user_name = frappe.db.get_value("User", user, "full_name") or user

	paths = ensure_runtime_dirs(frappe.local.site)

	soul = f"""You are a business automation engine for {company}'s Frappe/ERPNext system.

CRITICAL: You operate through OpenClaw for this site.
Use frappe_plan_request first for vague, multi-part, write-heavy, workflow-heavy, or analytical questions.
Use frappe_get_session_mode to inspect the current session mode.
Use frappe_set_session_mode only when the user explicitly asks to enter or exit admin mode.
Use frappe_search_site_context first when the user mentions a module, report, workflow, field, or app in natural language and the request is still metadata discovery.
Use frappe_retrieve_site_context when you need typed lexical retrieval across doctypes, reports, workflows, UI, scripts, or customizations.
Use frappe_get_site_manifest for concise site summaries or scoped manifest sections. Ask for full detail only when needed.
Use frappe_get_action_catalog only when you already know you need an action and want the exact action name.
Use frappe_prepare_create_record before creating a document from a vague request. It tells you which DocType to use, whether the user can create it, and which questions you must ask first.
Use frappe_validate_action before risky writes when permissions, schema, or validation may block the change.
Use frappe_execute_action for provider-driven work so permissions and validations run as the mapped ERP user.
Treat CRUD-style actions such as get_list, get_document, create_document, update_document, and delete_document as low-level execution primitives, not as the main reasoning surface for vague business requests.
Prefer planner results, context retrieval, workflow capabilities, report capabilities, and module-aware skills before dropping to low-level primitives.
If identity, permissions, session mode, or document scope are unclear, ask a follow-up question instead of stopping.
Prefer short answers first. Summarize before using more than one tool.
Do not answer inventory questions from frappe_search_site_context alone. That tool only tells you which doctypes, reports, and workflows exist.
If the user asks what records, documents, items, or transactions are present, first identify the DocType, then use frappe_execute_action with get_list or get_document.
If the user asks for actual report output or metrics, use frappe_execute_action with run_report instead of describing the report name.
Never invent action names. Only use exact names returned by frappe_get_action_catalog or the action_plan returned by frappe_prepare_create_record.
Every write requires confirmation before frappe_execute_action.
Customization work such as scripts, custom fields, property setters, workflow design, and funnel design requires explicit admin mode.
When frappe_plan_request returns scope, top_doctype, top_report, related_reports, or answer_constraints, treat that as the authoritative scope.
Do not list reports, modules, or doctypes outside that scoped set when answer_constraints restrict the answer.
If permission_summary.can_run_report is false, say so explicitly and offer a data-access fallback such as get_list on the focus DocType.

SITE SHAPE:
{module_ref}

RULES:
1. Multi-step or vague requests → call frappe_plan_request first, then follow its plan_steps
2. User asks to see data or understand a module → use frappe_search_site_context or frappe_retrieve_site_context first, then a focused read action
2a. Analytical questions should stay anchored to the planned focus DocType and scoped reports only
3. User asks to create or change data → use frappe_validate_action when helpful, ask for confirmation, then frappe_execute_action
3a. If the create request is vague or missing fields → use frappe_prepare_create_record first and ask the returned questions before attempting create_document
4. If the request touches scripts, custom fields, workflows, property setters, or funnels → require explicit admin mode before proposing or applying changes
5. If you get a "DocType not found" error → use discovery tools to find the correct DocType, report, or workflow
6. If you get "Unknown column" or validation errors → use get_doctype_meta or form metadata, then retry
7. NEVER guess field names. Use live metadata first.
8. Keep Telegram responses short, direct, and business-focused
9. Never reveal salary, passwords, API keys, or bank details
10. "What all X are present" means list actual records, not doctypes

Current user: {user_name}
Installed apps: {installed_apps}
"""

	soul_path = os.path.join(paths["workspace"], "SOUL.md")
	os.makedirs(os.path.dirname(soul_path), exist_ok=True)
	with open(soul_path, "w") as f:
		f.write(soul)

	return {
		"success": True,
		"path": soul_path,
		"modules": len(modules),
		"doctypes": len(doctypes),
		"preview": soul[:500],
	}


@frappe.whitelist()
def start_gateway():
	"""Start the OpenClaw gateway process."""
	from mcp_ui.openclaw.manager import start_gateway as _start
	pid = _start()
	if pid:
		return {"success": True, "pid": pid}
	return {"success": False, "error": "Failed to start gateway. Check logs."}


@frappe.whitelist()
def stop_gateway():
	"""Stop the OpenClaw gateway process."""
	from mcp_ui.openclaw.manager import stop_gateway as _stop
	stopped = _stop()
	return {"success": stopped}


@frappe.whitelist()
def gateway_status():
	"""Get the current gateway status."""
	from mcp_ui.openclaw.manager import get_status
	return get_status()


@frappe.whitelist()
def restart_gateway():
	"""Restart the OpenClaw gateway so updated config is applied immediately."""
	from mcp_ui.openclaw.manager import start_gateway as _start, stop_gateway as _stop

	_stop()
	pid = _start()
	if pid:
		return {"success": True, "pid": pid}
	return {"success": False, "error": "Failed to restart gateway. Check logs."}


@frappe.whitelist()
def create_playwright_session(user: str = "Administrator"):
	"""Create a local Desk session cookie for browser-based verification."""
	from frappe.auth import CookieManager, LoginManager
	from frappe.utils import set_request

	set_request(path="/")
	frappe.local.cookie_manager = CookieManager()
	frappe.local.login_manager = LoginManager()
	frappe.local.login_manager.login_as(user)

	return {
		"success": True,
		"user": frappe.session.user,
		"sid": frappe.session.sid,
		"full_name": frappe.session.data.get("full_name"),
	}


@frappe.whitelist()
def provision_telegram_user(
	frappe_user: str,
	full_name: str = "",
	telegram_username: str = "",
	external_id: str = "",
	site: str = "",
	send_welcome_email: int = 0,
	restart_gateway_after: int = 1,
):
	"""Create or update a Frappe user plus Telegram identity mapping from MCP Settings."""
	if not frappe_user:
		frappe.throw("Frappe User email is required")

	telegram_username = (telegram_username or "").strip().lstrip("@")
	external_id = (external_id or "").strip()
	if not telegram_username and not external_id:
		frappe.throw("Provide a Telegram username")

	site = site or frappe.local.site
	user, user_created = _ensure_frappe_user(
		email=frappe_user.strip(),
		full_name=full_name.strip(),
		send_welcome_email=bool(cint(send_welcome_email)),
	)

	settings = frappe.get_single("MCP Settings")
	identity_row, identity_created = _upsert_identity_mapping(
		settings=settings,
		frappe_user=user.name,
		site=site,
		telegram_username=telegram_username,
		external_id=external_id,
	)
	legacy_row, legacy_created = _upsert_legacy_telegram_mapping(
		settings=settings,
		frappe_user=user.name,
		telegram_username=telegram_username,
	)
	settings.save(ignore_permissions=True)
	frappe.db.commit()

	config_result = generate_config()
	restart_result = restart_gateway() if cint(restart_gateway_after) else None
	warnings = []
	if not external_id:
		warnings.append(
			"Telegram numeric ID is optional in the current setup. Access is enforced by Frappe-side federation using the mapped Telegram username and user email."
		)

	return {
		"success": True,
		"user_created": user_created,
		"user": {
			"name": user.name,
			"full_name": user.full_name,
			"enabled": user.enabled,
			"user_type": user.user_type,
		},
		"identity_mapping": {
			"created": identity_created,
			"name": identity_row.name,
			"channel": identity_row.channel,
			"external_id": identity_row.external_id,
			"external_username": identity_row.external_username,
			"frappe_user": identity_row.frappe_user,
			"site": identity_row.site,
		},
		"legacy_mapping": {
			"created": legacy_created,
			"name": getattr(legacy_row, "name", None),
			"telegram_username": getattr(legacy_row, "telegram_username", ""),
			"frappe_user": getattr(legacy_row, "frappe_user", ""),
		},
		"config_path": config_result.get("config_path"),
		"gateway": restart_result,
		"warnings": warnings,
	}


@frappe.whitelist()
def setup_openclaw():
	"""One-click setup: install npm packages, generate config, generate SOUL.md, start gateway."""
	from mcp_ui.openclaw.manager import install_openclaw, start_gateway as _start, get_status

	steps = []

	# Step 1: Install npm packages
	result = install_openclaw()
	steps.append({"step": "Install OpenClaw", "success": result.get("success"), "detail": result.get("error", "OK")})
	if not result.get("success"):
		return {"success": False, "steps": steps, "error": "npm install failed"}

	# Step 2: Generate config
	try:
		cfg = generate_config()
		steps.append({"step": "Generate Config", "success": True, "detail": cfg.get("config_path", "OK")})
	except Exception as e:
		steps.append({"step": "Generate Config", "success": False, "detail": str(e)})
		return {"success": False, "steps": steps, "error": str(e)}

	# Step 3: Start gateway
	pid = _start()
	steps.append({"step": "Start Gateway", "success": bool(pid), "detail": f"PID {pid}" if pid else "Failed"})

	return {
		"success": bool(pid),
		"steps": steps,
		"status": get_status(),
	}


def _get_openclaw_model(settings, provider_config) -> str:
	"""Convert MCP Settings provider config to OpenClaw model string."""
	provider = provider_config.get("provider") or settings.ai_provider or "OpenAI"
	model = provider_config.get("model", "")
	if not model:
		if provider == "OpenAI":
			model = settings.get("openai_model") or "gpt-4o-mini"
		elif provider == "Anthropic":
			model = settings.get("anthropic_model") or "claude-3-5-haiku-20241022"
		elif provider == "Ollama":
			model = settings.get("ai_chat_model") or "qwen3:8b"
		elif provider == "Google":
			model = settings.get("ai_chat_model") or "gemini-2.0-flash"

	if provider == "Ollama":
		# OpenClaw format: ollama/model_name
		return model.replace("ollama_chat/", "ollama/")
	elif provider == "OpenAI":
		return f"openai/{model}" if not model.startswith("openai/") else model
	elif provider == "Anthropic":
		return f"anthropic/{model}" if not model.startswith("anthropic/") else model
	elif provider == "Google":
		return f"google/{model}" if not model.startswith("google/") else model
	else:
		return model


def _get_env_key_name(provider: str) -> str:
	"""Get the environment variable name for the provider's API key."""
	mapping = {
		"OpenAI": "OPENAI_API_KEY",
		"Anthropic": "ANTHROPIC_API_KEY",
		"Google": "GEMINI_API_KEY",
	}
	return mapping.get(provider, "")


def _provider_requires_api_key(provider: str) -> bool:
	return provider not in {"", "Ollama"}


def _build_model_provider_config(settings, provider_config: dict) -> dict:
	provider = provider_config.get("provider") or settings.ai_provider or "OpenAI"
	api_key = (provider_config.get("api_key") or "").strip()
	api_base = (provider_config.get("api_base") or "").strip()

	if provider == "Ollama":
		model_name = _extract_ollama_model_name(provider_config.get("model") or settings.get("ai_chat_model") or "qwen3:8b")
		entry = {
			"baseUrl": api_base or (settings.get("ai_chat_base_url") or "http://localhost:11434"),
			"apiKey": api_key or "ollama-local",
			"api": "ollama",
			"models": [
				{
					"id": model_name,
					"name": model_name,
					"reasoning": False,
					"input": ["text"],
					"cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
					"contextWindow": 32768,
					"maxTokens": 32768,
				}
			],
		}
		return {"ollama": entry}

	if not api_key:
		return {}

	if provider == "OpenAI":
		entry = {"apiKey": api_key}
		if api_base:
			entry["baseUrl"] = api_base
		return {"openai": entry}

	if provider == "Anthropic":
		return {"anthropic": {"apiKey": api_key}}

	if provider == "Google":
		return {"google": {"apiKey": api_key}}

	custom_provider_id = _normalize_custom_provider_id(provider)
	entry = {"apiKey": api_key}
	if api_base:
		entry["baseUrl"] = api_base
	return {custom_provider_id: entry}


def _write_model_auth_profiles(paths: dict, settings, provider_config: dict) -> None:
	provider = provider_config.get("provider") or settings.ai_provider or "OpenAI"
	api_key = (provider_config.get("api_key") or "").strip()
	if not api_key:
		return

	provider_id = _normalize_provider_id(provider)
	auth_profile_path = os.path.join(paths["home"], ".openclaw", "agents", "main", "agent", "auth-profiles.json")
	os.makedirs(os.path.dirname(auth_profile_path), exist_ok=True)

	existing = {}
	try:
		with open(auth_profile_path) as handle:
			existing = json.load(handle) or {}
	except Exception:
		existing = {}

	profiles = existing.get("profiles") or {}
	profile_id = f"{provider_id}:default"
	profiles[profile_id] = {
		"type": "api_key",
		"provider": provider_id,
		"key": api_key,
	}
	existing["profiles"] = profiles

	with open(auth_profile_path, "w") as handle:
		json.dump(existing, handle, indent=2)


def _mask_model_provider_secrets(config: dict) -> None:
	for entry in (config.get("models", {}) or {}).get("providers", {}).values():
		if isinstance(entry, dict) and entry.get("apiKey"):
			entry["apiKey"] = "***masked***"


def _normalize_provider_id(provider: str) -> str:
	mapping = {
		"OpenAI": "openai",
		"Anthropic": "anthropic",
		"Google": "google",
		"Ollama": "ollama",
	}
	return mapping.get(provider, _normalize_custom_provider_id(provider))


def _normalize_custom_provider_id(provider: str) -> str:
	return "".join(ch.lower() if ch.isalnum() else "-" for ch in (provider or "custom")).strip("-") or "custom"


def _extract_ollama_model_name(model: str) -> str:
	if not model:
		return "qwen3:8b"
	return model.replace("ollama_chat/", "").replace("ollama/", "")


def _get_secret(settings, fieldname: str) -> str:
	try:
		value = settings.get_password(fieldname)
		if value:
			return value
	except Exception:
		pass

	value = settings.get(fieldname)
	if isinstance(value, str) and set(value) == {"*"}:
		return ""
	return value or ""


def _ensure_frappe_user(email: str, full_name: str = "", send_welcome_email: bool = False):
	existing = frappe.db.exists("User", email)
	if existing:
		user = frappe.get_doc("User", existing)
		if full_name and not user.full_name:
			first_name, last_name = _split_full_name(full_name)
			user.first_name = first_name
			user.last_name = last_name
			user.save(ignore_permissions=True)
		return user, False

	display_name = full_name or email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()
	first_name, last_name = _split_full_name(display_name)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"send_welcome_email": 1 if send_welcome_email else 0,
			"user_type": "System User",
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	return user, True


def _upsert_identity_mapping(settings, frappe_user: str, site: str, telegram_username: str = "", external_id: str = ""):
	normalized_username = telegram_username.strip().lstrip("@").lower()
	row = None
	for existing in settings.get("identity_mappings", []):
		if (existing.channel or "").strip().lower() != "telegram":
			continue
		existing_username = (existing.external_username or "").strip().lstrip("@").lower()
		if external_id and (existing.external_id or "").strip() == external_id:
			row = existing
			break
		if normalized_username and existing_username == normalized_username:
			row = existing
			break
		if existing.frappe_user == frappe_user and (existing.site or "") == site:
			row = existing
			break

	created = row is None
	if row is None:
		row = settings.append("identity_mappings", {})

	row.channel = "telegram"
	row.frappe_user = frappe_user
	row.site = site
	row.enabled = 1
	if telegram_username:
		row.external_username = telegram_username.strip().lstrip("@")
	if external_id:
		row.external_id = external_id

	return row, created


def _upsert_legacy_telegram_mapping(settings, frappe_user: str, telegram_username: str = ""):
	if not telegram_username:
		return None, False

	normalized_username = telegram_username.strip().lstrip("@").lower()
	row = None
	for existing in settings.get("telegram_user_mappings", []):
		existing_username = (existing.telegram_username or "").strip().lstrip("@").lower()
		if existing_username == normalized_username or existing.frappe_user == frappe_user:
			row = existing
			break

	created = row is None
	if row is None:
		row = settings.append("telegram_user_mappings", {})

	row.telegram_username = telegram_username.strip().lstrip("@")
	row.frappe_user = frappe_user
	row.enabled = 1
	return row, created


def _get_allowed_browser_hosts(site: str) -> list[str]:
	from urllib.parse import urlparse

	hosts = {"localhost", "127.0.0.1", site}
	host_name = (frappe.local.conf or {}).get("host_name")
	if isinstance(host_name, str) and host_name.strip():
		candidate = host_name.strip()
		if "://" in candidate:
			parsed = urlparse(candidate)
			if parsed.hostname:
				hosts.add(parsed.hostname)
		else:
			hosts.add(candidate.split(":")[0])
	return sorted(host for host in hosts if host)


def _split_full_name(full_name: str) -> tuple[str, str]:
	parts = [part for part in (full_name or "").strip().split() if part]
	if not parts:
		return "Telegram", "User"
	if len(parts) == 1:
		return parts[0], ""
	return parts[0], " ".join(parts[1:])
