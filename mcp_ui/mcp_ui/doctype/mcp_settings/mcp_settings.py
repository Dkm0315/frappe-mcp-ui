# Copyright (c) 2025, dhairya and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MCPSettings(Document):
	def before_load(self):
		"""Populate system status fields before loading"""
		from mcp_ui.utils.app_checker import (
			is_nextai_installed,
			get_available_workflows,
			get_openai_api_key,
			get_ai_provider
		)
		
		# Check NextAI status
		if is_nextai_installed():
			self.nextai_installed = "✓ Installed"
			workflows = get_available_workflows()
			self.nextai_workflows_available = f"{len(workflows)} workflows"
		else:
			self.nextai_installed = "✗ Not Installed"
			self.nextai_workflows_available = "N/A"
		
		# Check OpenAI key source
		if get_openai_api_key():
			if is_nextai_installed():
				try:
					chatnext_key = frappe.db.get_single_value('ChatNext Settings', 'openai_api_key')
					if chatnext_key and chatnext_key.strip():
						self.openai_key_source = "ChatNext Settings (Primary)"
					else:
						self.openai_key_source = "MCP Settings (Fallback)"
				except:
					self.openai_key_source = "MCP Settings"
			else:
				self.openai_key_source = "MCP Settings"
		else:
			self.openai_key_source = "Not Configured"
		
		# AI provider status
		provider = get_ai_provider()
		if provider != 'None':
			self.ai_provider_status = f"✓ {provider} Configured"
		else:
			self.ai_provider_status = "✗ Not Configured"

