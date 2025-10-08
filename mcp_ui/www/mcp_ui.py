"""
MCP UI Web Page Entry Point
Provides boot data for the React SPA
"""
import frappe

no_cache = 1


def get_context(context):
	"""Prepare context with boot data for React app"""
	frappe.db.commit()

	context.boot = {
		"user": frappe.session.user,
		"csrf_token": frappe.sessions.get_csrf_token(),
		"site_name": frappe.local.site,
		"user_image": frappe.db.get_value("User", frappe.session.user, "user_image"),
		"full_name": frappe.utils.get_fullname(frappe.session.user),
	}

	return context

