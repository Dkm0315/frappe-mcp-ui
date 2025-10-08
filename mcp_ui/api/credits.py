"""
Credit Management API
Handles credit balance, usage tracking, and cost calculation
"""
import json

import frappe


@frappe.whitelist()
def get_balance():
	"""Get current user's credit balance"""
	user = frappe.session.user

	# Try to get existing credit record
	credit_doc = frappe.db.get_value(
		"MCP User Credits",
		{"user": user},
		["balance", "total_purchased", "total_consumed"],
		as_dict=True,
	)

	if not credit_doc:
		# Create initial credit record with 100 free credits
		doc = frappe.get_doc(
			{
				"doctype": "MCP User Credits",
				"user": user,
				"balance": 100,
				"total_purchased": 100,
				"total_consumed": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return {"balance": 100, "total_purchased": 100, "total_consumed": 0}

	return credit_doc


@frappe.whitelist()
def deduct_credits(amount, tool_name, params):
	"""
	Deduct credits from user balance and log usage

	Args:
		amount: Number of credits to deduct
		tool_name: Name of the tool executed
		params: Tool parameters (will be logged)
	"""
	user = frappe.session.user
	amount = int(amount)

	# Get user credits
	credit_name = frappe.db.get_value("MCP User Credits", {"user": user})

	if not credit_name:
		frappe.throw("No credit account found. Please contact administrator.")

	doc = frappe.get_doc("MCP User Credits", credit_name)

	# Check if sufficient balance
	if doc.balance < amount:
		frappe.throw(f"Insufficient credits. Required: {amount}, Available: {doc.balance}")

	# Deduct credits
	doc.balance -= amount
	doc.total_consumed += amount
	doc.save(ignore_permissions=True)

	# Log usage
	usage_log = frappe.get_doc(
		{
			"doctype": "MCP Usage Log",
			"user": user,
			"tool_name": tool_name,
			"credits_consumed": amount,
			"status": "Success",
			"input_params": json.dumps(params) if isinstance(params, dict) else str(params),
		}
	)
	usage_log.insert(ignore_permissions=True)

	frappe.db.commit()

	return {"success": True, "remaining_balance": doc.balance}


@frappe.whitelist()
def get_usage_history(limit=50):
	"""Get usage history for current user"""
	user = frappe.session.user

	logs = frappe.get_all(
		"MCP Usage Log",
		filters={"user": user},
		fields=["name", "tool_name", "credits_consumed", "status", "creation", "input_params", "output", "error_message"],
		order_by="creation desc",
		limit=int(limit),
	)

	return logs


@frappe.whitelist()
def calculate_tool_cost(tool_name, params=None):
	"""
	Calculate the cost of executing a tool

	Args:
		tool_name: Name of the tool
		params: Tool parameters (used for complexity calculation)

	Returns:
		Estimated credit cost
	"""
	params = params or {}

	# Base costs for different operations
	base_costs = {
		"create_document": 3,
		"update_document": 2,
		"delete_document": 2,
		"get_document": 1,
		"get_list": 1,
		"search_documents": 2,
		"execute_report": 5,
		"bulk_update": 10,
		"export_data": 5,
		"get_dashboard_data": 2,
	}

	# Get base cost
	cost = base_costs.get(tool_name, 5)

	# Adjust based on parameters
	if isinstance(params, dict):
		# Increase cost for bulk operations
		if "limit" in params:
			limit = int(params.get("limit", 20))
			cost += max(0, (limit - 20) // 10)  # +1 credit per 10 records above 20

		# Increase for complex filters
		if "filters" in params and isinstance(params["filters"], dict):
			filter_count = len(params["filters"])
			cost += filter_count // 3  # +1 credit per 3 filters

	return cost


@frappe.whitelist()
def purchase_credits(package_name):
	"""
	Purchase credit package
	Note: This is a placeholder. Implement actual payment integration.

	Args:
		package_name: Name of the credit package to purchase
	"""
	user = frappe.session.user

	# Get package details
	package = frappe.get_doc("MCP Credit Package", package_name)

	if not package.is_active:
		frappe.throw("This package is not available")

	# Get or create user credits
	credit_name = frappe.db.get_value("MCP User Credits", {"user": user})

	if not credit_name:
		doc = frappe.get_doc(
			{
				"doctype": "MCP User Credits",
				"user": user,
				"balance": 0,
				"total_purchased": 0,
				"total_consumed": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		credit_name = doc.name

	# Add credits (In production, this should be after payment confirmation)
	doc = frappe.get_doc("MCP User Credits", credit_name)
	doc.balance += package.credits
	doc.total_purchased += package.credits
	doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"success": True,
		"message": f"Added {package.credits} credits",
		"new_balance": doc.balance,
		"package": package.package_name,
		"price": package.price,
	}


@frappe.whitelist()
def get_available_packages():
	"""Get list of available credit packages"""
	packages = frappe.get_all(
		"MCP Credit Package",
		filters={"is_active": 1},
		fields=["name", "package_name", "credits", "price", "description"],
		order_by="price asc",
	)

	return packages

