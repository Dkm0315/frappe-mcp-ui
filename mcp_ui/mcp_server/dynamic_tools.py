"""
Dynamic MCP Tools Generator
Auto-generates tools based on installed DocTypes
"""
import frappe


def register_dynamic_tools():
	"""
	Dynamically register tools for each DocType
	This can be expanded to auto-generate CRUD tools for specific DocTypes
	"""
	# For now, we rely on core_tools for generic operations
	# In future, this can generate DocType-specific tools with proper schemas
	pass


# Call on module load
register_dynamic_tools()

