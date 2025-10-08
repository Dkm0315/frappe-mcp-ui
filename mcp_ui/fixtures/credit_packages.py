"""
Default Credit Packages
"""

DEFAULT_PACKAGES = [
	{
		"doctype": "MCP Credit Package",
		"package_name": "Starter Pack",
		"credits": 100,
		"price": 10.00,
		"is_active": 1,
		"description": "Perfect for trying out MCP tools"
	},
	{
		"doctype": "MCP Credit Package",
		"package_name": "Professional Pack",
		"credits": 500,
		"price": 40.00,
		"is_active": 1,
		"description": "For regular users and small teams"
	},
	{
		"doctype": "MCP Credit Package",
		"package_name": "Business Pack",
		"credits": 1000,
		"price": 75.00,
		"is_active": 1,
		"description": "Best value for businesses"
	},
	{
		"doctype": "MCP Credit Package",
		"package_name": "Enterprise Pack",
		"credits": 5000,
		"price": 300.00,
		"is_active": 1,
		"description": "For large-scale operations"
	},
]


def install_packages():
	"""Install default credit packages"""
	import frappe

	for package_data in DEFAULT_PACKAGES:
		if not frappe.db.exists("MCP Credit Package", package_data["package_name"]):
			doc = frappe.get_doc(package_data)
			doc.insert(ignore_permissions=True)
			frappe.logger().info(f"Created credit package: {package_data['package_name']}")

	frappe.db.commit()

