"""
App Detection and Configuration Utilities
Handles optional NextAI integration and OpenAI key fallback
"""
import frappe
from typing import Optional, List, Dict, Any


def is_nextai_installed() -> bool:
	"""
	Check if nextai app is installed
	
	Returns:
		bool: True if nextai is in installed apps
	"""
	try:
		return "nextai" in frappe.get_installed_apps()
	except Exception:
		return False


def get_openai_api_key() -> Optional[str]:
	"""
	Get OpenAI API key with fallback chain:
	1. Try ChatNext Settings (if nextai installed and configured)
	2. Fall back to MCP Settings
	3. Return None if neither configured
	
	Returns:
		Optional[str]: OpenAI API key or None
	"""
	# Try ChatNext Settings first if nextai is installed
	if is_nextai_installed():
		try:
			key = frappe.db.get_single_value('ChatNext Settings', 'openai_api_key')
			if key and key.strip():
				return key
		except Exception:
			# ChatNext Settings might not exist or field might not be accessible
			pass
	
	# Fallback to MCP Settings
	try:
		key = frappe.db.get_single_value('MCP Settings', 'openai_api_key')
		if key and key.strip():
			return key
	except Exception:
		pass
	
	return None


def get_anthropic_api_key() -> Optional[str]:
	"""
	Get Anthropic API key with fallback chain:
	1. Try MCP Settings first (our primary config)
	2. Return None if not configured
	
	Returns:
		Optional[str]: Anthropic API key or None
	"""
	try:
		key = frappe.db.get_single_value('MCP Settings', 'anthropic_api_key')
		if key and key.strip():
			return key
	except Exception:
		pass
	
	return None


def get_ai_provider() -> str:
	"""
	Get configured AI provider
	
	Returns:
		str: 'OpenAI', 'Anthropic', or 'None'
	"""
	try:
		settings = frappe.get_single('MCP Settings')
		if settings.enable_ai_nlp and settings.ai_provider:
			return settings.ai_provider
	except Exception:
		pass
	
	return 'None'


def get_available_workflows() -> List[Dict[str, Any]]:
	"""
	Get Funnel workflows if nextai installed
	
	Returns:
		List[Dict]: List of published workflows or empty list
	"""
	if not is_nextai_installed():
		return []
	
	try:
		workflows = frappe.get_all(
			"Funnel Published",
			filters={"published": 1},
			fields=["name", "funnel", "funnel_description", "modified"],
			order_by="modified desc"
		)
		return workflows
	except Exception as e:
		frappe.log_error(f"Error fetching workflows: {str(e)}")
		return []


def get_nextai_features() -> Dict[str, bool]:
	"""
	Get available NextAI features
	
	Returns:
		Dict with feature availability flags
	"""
	if not is_nextai_installed():
		return {
			"installed": False,
			"workflows": False,
			"bulk_actions": False,
			"whatsapp": False,
			"chatnext": False
		}
	
	try:
		# Check if ChatNext is enabled
		chatnext_enabled = False
		try:
			chatnext_enabled = frappe.db.get_single_value('ChatNext Settings', 'enable_chat_assistant') or False
		except:
			pass
		
		return {
			"installed": True,
			"workflows": len(get_available_workflows()) > 0,
			"bulk_actions": frappe.db.exists("DocType", "ChatNext Bulk Action"),
			"whatsapp": frappe.db.exists("DocType", "WhatsApp Message"),
			"chatnext": chatnext_enabled
		}
	except Exception as e:
		frappe.log_error(f"Error checking NextAI features: {str(e)}")
		return {
			"installed": True,
			"workflows": False,
			"bulk_actions": False,
			"whatsapp": False,
			"chatnext": False
		}


@frappe.whitelist()
def get_system_health():
	"""
	Get overall system health and configuration status
	
	Returns:
		Dict with system health information
	"""
	return {
		"nextai": {
			"installed": is_nextai_installed(),
			"features": get_nextai_features()
		},
		"ai": {
			"openai_configured": get_openai_api_key() is not None,
			"anthropic_configured": get_anthropic_api_key() is not None,
			"provider": get_ai_provider(),
			"openai_source": "ChatNext Settings" if (is_nextai_installed() and frappe.db.get_single_value('ChatNext Settings', 'openai_api_key')) else "MCP Settings"
		},
		"apps": frappe.get_installed_apps(),
		"mcp_ui_version": frappe.get_attr("mcp_ui.__version__") if hasattr(frappe.get_module("mcp_ui"), "__version__") else "1.0.0"
	}

