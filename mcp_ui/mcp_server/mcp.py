"""
MCP Server for Frappe UI
Main MCP instance and endpoint registration
"""
import frappe_mcp

# Create MCP instance
mcp = frappe_mcp.MCP("frappe-mcp-ui")


@mcp.register()
def handle_mcp():
	"""
	MCP endpoint handler
	Endpoint: /api/method/mcp_ui.mcp_server.mcp.handle_mcp
	"""
	# Import tools to register them
	from mcp_ui.mcp_server import core_tools  # noqa: F401
	from mcp_ui.mcp_server import dynamic_tools  # noqa: F401

