"""Source parsers for customization discovery."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def safe_read_text(path: str | Path) -> str:
	try:
		return Path(path).read_text(encoding="utf-8")
	except Exception:
		return ""


def parse_python_controller(path: str | Path) -> dict[str, Any]:
	source = safe_read_text(path)
	if not source:
		return {
			"path": str(path),
			"class_names": [],
			"methods": [],
			"rules": [],
			"whitelisted_methods": [],
			"whitelisted_signatures": {},
		}

	class_names: list[str] = []
	methods: list[str] = []
	rules: list[dict[str, str]] = []
	whitelisted_methods: list[str] = []
	whitelisted_signatures: dict[str, dict[str, Any]] = {}
	try:
		tree = ast.parse(source)
	except Exception:
		return {
			"path": str(path),
			"class_names": [],
			"methods": [],
			"rules": [],
			"whitelisted_methods": [],
			"whitelisted_signatures": {},
		}

	for node in tree.body:
		if isinstance(node, ast.ClassDef):
			class_names.append(node.name)
			for child in node.body:
				if not isinstance(child, ast.FunctionDef):
					continue
				methods.append(child.name)
				if child.name in {
					"validate",
					"before_save",
					"before_submit",
					"on_submit",
					"on_update",
					"before_cancel",
					"on_cancel",
				}:
					rules.append({"event": child.name, "action": f"{child.name} in {Path(path).name}"})
		elif isinstance(node, ast.FunctionDef):
			methods.append(node.name)
			decorators = [
				ast.unparse(decorator) if hasattr(ast, "unparse") else ""
				for decorator in node.decorator_list
			]
			if any("frappe.whitelist" in decorator for decorator in decorators):
				whitelisted_methods.append(node.name)
				whitelisted_signatures[node.name] = _extract_function_signature(node)
			if node.name in {
				"validate",
				"before_save",
				"before_submit",
				"on_submit",
				"on_update",
				"before_cancel",
				"on_cancel",
			}:
				rules.append({"event": node.name, "action": f"{node.name} in {Path(path).name}"})
	return {
		"path": str(path),
		"class_names": class_names,
		"methods": sorted(set(methods)),
		"rules": rules,
		"whitelisted_methods": sorted(set(whitelisted_methods)),
		"whitelisted_signatures": whitelisted_signatures,
	}


def parse_hooks_file(path: str | Path) -> dict[str, Any]:
	source = safe_read_text(path)
	if not source:
		return {"path": str(path), "doc_events": {}, "scheduler_events": {}, "override_whitelisted_methods": {}}

	result = {"path": str(path), "doc_events": {}, "scheduler_events": {}, "override_whitelisted_methods": {}}
	try:
		tree = ast.parse(source)
	except Exception:
		return result

	for node in tree.body:
		if isinstance(node, ast.Assign) and node.targets:
			target = node.targets[0]
			if not isinstance(target, ast.Name):
				continue
			if target.id in result:
				try:
					result[target.id] = ast.literal_eval(node.value)
				except Exception:
					result[target.id] = {}
	return result


def extract_rule_snippets(source: str) -> list[dict[str, str]]:
	rules = []
	for line in source.splitlines():
		text = line.strip()
		if not text or text.startswith("#"):
			continue
		if re.search(r"\bif\b|frappe\.throw|validate|workflow_state|reqd|required", text, flags=re.I):
			rules.append({"condition": text[:220], "action": "runtime_validation"})
	return rules[:25]


def infer_doctype_from_controller_path(path: str | Path) -> str:
	parts = Path(path).parts
	if "doctype" not in parts:
		return ""
	idx = parts.index("doctype")
	if idx + 1 < len(parts):
		return parts[idx + 1].replace("_", " ").title()
	return ""


def _extract_function_signature(node: ast.FunctionDef) -> dict[str, Any]:
	positional = [arg.arg for arg in node.args.posonlyargs + node.args.args]
	kwonly = [arg.arg for arg in node.args.kwonlyargs]
	default_count = len(node.args.defaults)
	required_positional = positional[: max(len(positional) - default_count, 0)]
	optional_positional = positional[max(len(positional) - default_count, 0):]
	required_kwonly = [
		arg_name
		for arg_name, default in zip(kwonly, node.args.kw_defaults)
		if default is None
	]
	optional_kwonly = [
		arg_name
		for arg_name, default in zip(kwonly, node.args.kw_defaults)
		if default is not None
	]
	return {
		"parameters": [
			name
			for name in [*positional, *kwonly]
			if name not in {"self", "cls"}
		],
		"required_params": [
			name
			for name in [*required_positional, *required_kwonly]
			if name not in {"self", "cls"}
		],
		"optional_params": [
			name
			for name in [*optional_positional, *optional_kwonly]
			if name not in {"self", "cls"}
		],
		"accepts_kwargs": bool(node.args.kwarg),
	}
