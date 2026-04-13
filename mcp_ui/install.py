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
		from mcp_ui.openclaw.site_context import refresh_site_context
		from mcp_ui.api.openclaw import generate_config

		result = install_openclaw()
		if result.get("success"):
			frappe.logger().info("OpenClaw npm packages installed successfully")
		else:
			frappe.logger().warning(
				f"OpenClaw install skipped: {result.get('error')}. "
				"Run 'Setup OpenClaw' from MCP Settings to install later."
			)

		try:
			refresh_site_context(reason="after_install")
			generate_config()
		except Exception as inner_exc:
			frappe.logger().warning(f"OpenClaw context bootstrap skipped: {inner_exc}")
	except Exception as e:
		frappe.logger().warning(f"OpenClaw install skipped: {e}")

	frappe.logger().info("MCP UI app installed successfully!")
