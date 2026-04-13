from __future__ import annotations

import re
import shutil
from pathlib import Path

from mcp_ui.openclaw.runtime import ensure_runtime_dirs


def _slug(value: str) -> str:
	slug = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
	return slug or "skill"


def _write_skill(path: Path, name: str, description: str, body: str) -> None:
	path.mkdir(parents=True, exist_ok=True)
	content = f"""---
name: {name}
description: {description}
---

{body}
"""
	(path / "SKILL.md").write_text(content)


def generate_site_skills(manifest: dict) -> list[str]:
	paths = ensure_runtime_dirs(manifest.get("site"))
	skills_root = Path(paths["skills_dir"])

	for child in skills_root.iterdir():
		if child.is_dir():
			shutil.rmtree(child)

	created = []
	system = manifest.get("system", {})
	apps = manifest.get("apps", [])

	overview_body = "\n".join(
		[
			f"This workspace is attached to Frappe site `{manifest.get('site')}`.",
			"Use `frappe_plan_request` first for vague, multi-step, write-heavy, or analytical requests.",
			"Use `frappe_search_site_context` for flat metadata discovery and `frappe_retrieve_site_context` for typed grouped retrieval.",
			"Use `frappe_get_site_manifest` for concise summaries or targeted sections instead of full dumps.",
			"Use `frappe_get_change_summary` when the user asks what changed after updates or git pulls.",
			"Use `frappe_get_session_mode` to inspect the current mode and `frappe_set_session_mode` only when the user explicitly asks to enter or exit admin mode.",
			"Use `frappe_get_action_catalog` only when you need the exact action name for a write or workflow step.",
			"Use `frappe_execute_action` for provider-driven actions so permissions, validations, audit logging, confirmation gates, and mode gates stay user-scoped.",
			"Ask follow-up questions whenever a request is ambiguous, missing a document identifier, or spans multiple modules.",
			"",
			f"Installed apps: {', '.join(app['name'] for app in apps[:20])}",
			f"Total doctypes: {system.get('counts', {}).get('doctypes', 0)}",
			f"Total workflows: {system.get('counts', {}).get('workflows', 0)}",
			f"Total custom fields: {system.get('counts', {}).get('custom_fields', 0)}",
		]
	)
	overview_name = "frappe-site-overview"
	_write_skill(
		skills_root / overview_name,
		overview_name,
		"Operate against the current Frappe site with permissions, workflow, UI, and customization awareness.",
		overview_body,
	)
	created.append(overview_name)

	for app in apps:
		modules = app.get("modules", [])
		skill_name = f"app-{_slug(app['name'])}"
		body = "\n".join(
			[
				f"Use this skill when the user is asking about the `{app['name']}` app.",
				"Start by checking the live manifest instead of assuming stock ERPNext behavior.",
				"Call `frappe_plan_request` first when the request is broad or multi-step.",
				"Call `frappe_search_site_context` or `frappe_retrieve_site_context` first to find the right doctypes, reports, workflows, pages, and customizations inside this app.",
				"Call `frappe_get_site_manifest` only for concise summaries or targeted sections.",
				"Call `frappe_get_change_summary` if the user is asking about newly deployed changes.",
				"Use `frappe_get_action_catalog` only when you need the exact action name for a change.",
				"Use `frappe_execute_action` for changes that affect documents, scripts, workflows, or custom fields, but only after explicit confirmation for writes.",
				"",
				f"Modules: {', '.join(modules[:25]) or 'No modules discovered'}",
				f"Git ref: {app.get('git_ref') or 'unknown'}",
			]
		)
		_write_skill(
			skills_root / skill_name,
			skill_name,
			f"Understand business logic and customizations for the {app['name']} app.",
			body,
		)
		created.append(skill_name)

	return created
