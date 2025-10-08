"""
Installation script for MCP UI
"""
import frappe


def after_install():
	"""Run after app installation"""
	from mcp_ui.fixtures.credit_packages import install_packages

	# Install default credit packages
	install_packages()

	frappe.logger().info("MCP UI app installed successfully!")

