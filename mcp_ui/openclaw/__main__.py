"""
Entry point: python -m mcp_ui.openclaw
Starts the Frappe MCP server for OpenClaw integration.
"""
import asyncio
from mcp_ui.openclaw.server import run

if __name__ == "__main__":
	asyncio.run(run())
