"""
Installation script for MCP UI
"""
import frappe


def after_install():
	"""Run after app installation."""
	from mcp_ui.fixtures.credit_packages import install_packages

	# Install default credit packages
	install_packages()

	# Install OpenClaw npm packages (non-blocking — logs errors but doesn't fail install)
	try:
		from mcp_ui.openclaw.manager import install_openclaw
		result = install_openclaw()
		if result.get("success"):
			frappe.logger().info("OpenClaw npm packages installed successfully")
		else:
			frappe.logger().warning(
				f"OpenClaw install skipped: {result.get('error')}. "
				"Run 'Setup OpenClaw' from MCP Settings to install later."
			)
	except Exception as e:
		frappe.logger().warning(f"OpenClaw install skipped: {e}")

	# Initialize the intent-layer schema and customization registry.
	try:
		from mcp_ui.intent_layer.api import refresh_schema

		refresh_schema()
		frappe.logger("intent_layer").info("Intent Layer registry initialized successfully")
	except Exception as e:
		frappe.logger("intent_layer").warning(f"Intent Layer schema refresh skipped: {e}")

	frappe.logger().info("MCP UI app installed successfully!")
