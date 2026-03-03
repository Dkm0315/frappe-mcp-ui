"""
OpenClaw Configuration API
Generates openclaw.json, manages Telegram user mappings, health checks.
"""
import json
import os

import frappe

from mcp_ui.ai.providers import get_provider_config


@frappe.whitelist()
def generate_config():
	"""
	Generate ~/.openclaw/openclaw.json with correct OpenClaw schema.

	Uses the openclaw-mcp-adapter plugin to bridge our Frappe MCP server
	into native OpenClaw agent tools. Also generates SOUL.md dynamically.
	"""
	import secrets

	settings = frappe.get_single("MCP Settings")
	provider_config = get_provider_config()

	bench_path = frappe.utils.get_bench_path()
	python_path = os.path.join(bench_path, "env", "bin", "python")
	site = frappe.local.site

	# Build model string for OpenClaw
	model = _get_openclaw_model(settings, provider_config)
	provider = settings.ai_provider or "OpenAI"

	# Build the config — only keys OpenClaw actually accepts
	config = {
		"agents": {
			"defaults": {
				"model": model,
				"compaction": {"mode": "safeguard"},
			},
		},
		"commands": {
			"native": "auto",
			"nativeSkills": "auto",
			"restart": True,
			"ownerDisplay": "raw",
		},
		"channels": {},
		"gateway": {
			"mode": "local",
			"auth": {
				"mode": "token",
				"token": secrets.token_hex(24),
			},
		},
		"plugins": {
			"entries": {
				"openclaw-mcp-adapter": {
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
									"FRAPPE_USER": frappe.session.user,
								},
							}
						],
					},
				},
			},
		},
	}

	# Add Telegram channel if configured
	telegram_token = settings.get("telegram_bot_token")
	if telegram_token:
		config["channels"]["telegram"] = {
			"enabled": True,
			"botToken": telegram_token,
			"dmPolicy": "open",
			"allowFrom": ["*"],
			"groupPolicy": "allowlist",
			"textChunkLimit": 4000,
			"streaming": "partial",
		}

	# Save to ~/.openclaw/openclaw.json (where OpenClaw actually reads it)
	openclaw_dir = os.path.expanduser("~/.openclaw")
	os.makedirs(openclaw_dir, exist_ok=True)
	config_path = os.path.join(openclaw_dir, "openclaw.json")
	with open(config_path, "w") as f:
		json.dump(config, f, indent=2)

	# Also generate SOUL.md dynamically from the live Frappe system
	soul_result = generate_soul_md()

	# Build setup instructions
	env_key = _get_env_key_name(provider)
	instructions = [
		f"Config saved to: {config_path}",
		f"SOUL.md generated: {soul_result.get('path', '~/.openclaw/workspace/SOUL.md')}",
		"",
		"Setup steps:",
		"1. Install OpenClaw: npm install -g openclaw",
		"2. Install MCP adapter: cd ~/.openclaw && mkdir -p extensions && cd extensions && npm install openclaw-mcp-adapter",
	]
	if provider == "Ollama":
		instructions.append("3. Start Ollama: ollama serve")
		instructions.append(f"4. Pull model: ollama pull {provider_config.get('model', 'qwen3:8b')}")
		instructions.append("5. Run: OLLAMA_API_KEY=ollama-local openclaw gateway")
	elif env_key:
		instructions.append(f"3. Set API key: export {env_key}='your-api-key'")
		instructions.append("4. Run: openclaw gateway")
	else:
		instructions.append("3. Run: openclaw gateway")

	# Build a display-safe version (mask secrets)
	safe_config = json.loads(json.dumps(config))
	if telegram_token:
		safe_config["channels"]["telegram"]["botToken"] = "***masked***"
	safe_config["gateway"]["auth"]["token"] = "***masked***"

	return {
		"success": True,
		"config_path": config_path,
		"config": safe_config,
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
	"""Look up the Frappe user mapped to a Telegram username."""
	settings = frappe.get_single("MCP Settings")
	for mapping in settings.get("telegram_user_mappings", []):
		if mapping.telegram_username == telegram_username and mapping.enabled:
			user = frappe.get_doc("User", mapping.frappe_user)
			return {
				"success": True,
				"frappe_user": mapping.frappe_user,
				"full_name": user.full_name,
				"roles": [r.role for r in user.roles],
			}
	return {"success": False, "error": f"No mapping for Telegram user: {telegram_username}"}


@frappe.whitelist()
def get_openclaw_status():
	"""Health check: verify OpenClaw configuration is complete."""
	settings = frappe.get_single("MCP Settings")
	issues = []

	if not settings.get("ai_chat_enabled"):
		issues.append("AI Chat is not enabled")
	if not settings.get("openclaw_enabled"):
		issues.append("OpenClaw is not enabled")
	if not settings.get("telegram_bot_token"):
		issues.append("Telegram Bot Token is not set")
	if not settings.get("telegram_user_mappings"):
		issues.append("No Telegram user mappings configured")

	# Check if MCP server tools load
	try:
		from mcp_ui.ai.tools import get_tool_schemas
		tool_count = len(get_tool_schemas())
	except Exception as e:
		tool_count = 0
		issues.append(f"MCP tools failed to load: {str(e)}")

	from mcp_ui.ai.providers import get_provider_config
	provider_config = get_provider_config()
	if not provider_config.get("model"):
		issues.append("No AI model configured")

	return {
		"success": len(issues) == 0,
		"tool_count": tool_count,
		"provider": settings.ai_provider or "Not set",
		"model": provider_config.get("model", "Not set"),
		"telegram_configured": bool(settings.get("telegram_bot_token")),
		"user_mappings": len(settings.get("telegram_user_mappings", [])),
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

	# Build the DocType reference section
	dt_lines = []
	# Priority modules first
	priority = ["Helpdesk", "Selling", "Buying", "Stock", "Accounts", "HR", "Projects", "CRM", "Core"]
	seen = set()
	for mod in priority:
		if mod in modules:
			names = ", ".join(f'"{n}"' for n in modules[mod][:15])
			dt_lines.append(f"- **{mod}**: {names}")
			seen.add(mod)

	# Then the rest
	for mod in sorted(modules.keys()):
		if mod not in seen and len(modules[mod]) > 0:
			names = ", ".join(f'"{n}"' for n in modules[mod][:10])
			dt_lines.append(f"- {mod}: {names}")

	dt_ref = "\n".join(dt_lines)

	# Get installed apps
	installed_apps = ", ".join(frappe.get_installed_apps())

	# Get current user info
	user = frappe.session.user
	user_name = frappe.db.get_value("User", user, "full_name") or user

	soul = f"""You are a business automation engine for {company}'s Frappe/ERPNext system.

CRITICAL: You EXECUTE actions using your frappe_* tools. NEVER give generic advice.

DOCTYPES IN THIS SYSTEM (use these EXACT names):
{dt_ref}

RULES:
1. User asks to see data → call frappe_get_list immediately with correct DocType name from above
2. User asks to create something → call frappe_create_document immediately
3. If you get a "DocType not found" error → call frappe_get_module_context to discover the right name
4. If you get "Unknown column" error → call frappe_get_doctype_meta to discover field names, then retry
5. NEVER guess field names. Use frappe_get_doctype_meta to look them up first.
6. Keep Telegram responses short with bullet points and bold
7. Never reveal salary, passwords, API keys, or bank details

Current user: {user_name}
Installed apps: {installed_apps}
"""

	# Write to ~/.openclaw/workspace/SOUL.md
	soul_path = os.path.expanduser("~/.openclaw/workspace/SOUL.md")
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
	provider = settings.ai_provider or "OpenAI"
	model = provider_config.get("model", "")

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
