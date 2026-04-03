"""Vectorless reasoning over semantic candidates and customization rules."""

from __future__ import annotations

from typing import Any

from mcp_ui.intent_layer.models.customization import CustomizationRegistry
from mcp_ui.intent_layer.models.semantic import SemanticRegistry, SemanticResult
from mcp_ui.intent_layer.utils.graph import RelationshipGraph


class ReasoningEngine:
	"""Choose a single execution path and prune invalid semantic candidates."""

	def reason(self, semantic_payload: dict[str, Any], customization_payload: dict[str, Any]) -> dict[str, Any]:
		semantic_result = semantic_payload
		semantic_registry = SemanticRegistry.from_dict(semantic_result.get("registry") or {})
		customization_registry = CustomizationRegistry.from_dict(customization_payload)
		intent = semantic_result.get("intent") or {}
		context = semantic_result.get("context") or {}
		candidates = list(semantic_result.get("candidates") or [])

		selected = self._select_candidate(candidates, context)
		context_target = context.get("resolved_target") or ""
		selected_target = selected.get("doctype") if selected else context_target
		if selected_target and selected_target not in semantic_registry.doctypes:
			selected_target = ""
		action = str(intent.get("action") or "unknown").lower()
		selected_doc = context.get("resolved_doc") or intent.get("entities", {}).get("document_name") or ""
		secondary_targets = self._resolve_secondary_targets(intent, candidates, selected_target)
		preferred_api = self._select_custom_api(
			customization_registry=customization_registry,
			selected_target=selected_target,
			action=action,
			entities=dict(intent.get("entities") or {}),
			selected_doc=selected_doc,
		)
		workflow = semantic_registry.workflows.get(selected_target, {})
		dependencies = self._resolve_dependencies(
			selected_target=selected_target,
			secondary_targets=secondary_targets,
			selected_doc=selected_doc,
			registry=semantic_registry,
		)

		valid_candidates = [
			{
				"doctype": candidate.get("doctype"),
				"score": candidate.get("score", 0.0),
				"matched_alias": candidate.get("matched_alias") or "",
			}
			for candidate in candidates
			if candidate.get("doctype") in semantic_registry.doctypes
		]
		score_gap = 1.0
		if len(valid_candidates) > 1:
			score_gap = float(valid_candidates[0].get("score") or 0.0) - float(valid_candidates[1].get("score") or 0.0)
		ambiguous_target = bool(intent.get("ambiguity")) and len(valid_candidates) > 1 and score_gap < 0.1
		return {
			"selected_target": selected_target,
			"selected_doc": selected_doc,
			"action": action,
			"entities": dict(intent.get("entities") or {}),
			"secondary_targets": secondary_targets,
			"preferred_api": preferred_api,
			"workflow": workflow,
			"dependencies": dependencies,
			"valid_candidates": valid_candidates,
			"confidence": selected.get("score", 0.0) if selected else 0.0,
			"ambiguity": ambiguous_target or not selected_target or action == "unknown",
		}

	def _select_candidate(self, candidates: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
		resolved_target = context.get("resolved_target")
		if resolved_target:
			for candidate in candidates:
				if candidate.get("doctype") == resolved_target:
					return candidate
		return candidates[0] if candidates else {}

	def _resolve_secondary_targets(
		self,
		intent: dict[str, Any],
		candidates: list[dict[str, Any]],
		selected_target: str,
	) -> list[str]:
		entities = dict(intent.get("entities") or {})
		secondary_targets = [
			target
			for target in entities.get("secondary_targets") or []
			if target and target != selected_target
		]
		if intent.get("action") == "create":
			for candidate in candidates:
				doctype = candidate.get("doctype")
				if doctype and doctype != selected_target and doctype == "Payment Entry":
					if doctype not in secondary_targets:
						secondary_targets.append(doctype)
		return secondary_targets

	def _select_custom_api(
		self,
		customization_registry: CustomizationRegistry,
		selected_target: str,
		action: str,
		entities: dict[str, Any],
		selected_doc: str,
	) -> dict[str, Any]:
		allowed_actions = {action}
		if action in {"list", "search", "read"}:
			allowed_actions = {"read", "list", "search"}
		elif action in {"approve", "reject", "submit", "workflow"}:
			allowed_actions = {"workflow", action}
		elif action == "unknown":
			allowed_actions = {"custom"}

		for method, row in customization_registry.api_map.items():
			if row.get("doctype") != selected_target or row.get("action") not in allowed_actions:
				continue
			if not self._api_signature_matches(row, entities=entities, selected_doc=selected_doc, selected_target=selected_target):
				continue
			return {
				"method": method,
				"action": row.get("action") or action,
				"doctype": selected_target,
				"parameters": row.get("parameters") or [],
				"required_params": row.get("required_params") or [],
				"accepts_kwargs": bool(row.get("accepts_kwargs")),
			}
		if action == "pay":
			for method, row in customization_registry.api_map.items():
				if row.get("action") != "pay" or (selected_target and row.get("doctype") != selected_target):
					continue
				if not self._api_signature_matches(row, entities=entities, selected_doc=selected_doc, selected_target=selected_target):
					continue
				return {
					"method": method,
					"action": "pay",
					"doctype": row.get("doctype") or selected_target,
					"parameters": row.get("parameters") or [],
					"required_params": row.get("required_params") or [],
					"accepts_kwargs": bool(row.get("accepts_kwargs")),
				}
		return {}

	def _api_signature_matches(
		self,
		api_row: dict[str, Any],
		entities: dict[str, Any],
		selected_doc: str,
		selected_target: str,
	) -> bool:
		required_params = [
			param
			for param in api_row.get("required_params") or []
			if param not in {"cmd", "method"}
		]
		available_params = set((entities or {}).keys())
		if selected_doc:
			available_params.add("name")
			available_params.add("docname")
		if selected_target:
			available_params.add("doctype")
			available_params.add("dt")
		return all(param in available_params for param in required_params)

	def _resolve_dependencies(
		self,
		selected_target: str,
		secondary_targets: list[str],
		selected_doc: str,
		registry: SemanticRegistry,
	) -> list[dict[str, Any]]:
		graph = RelationshipGraph(adjacency=registry.graph)
		dependencies: list[dict[str, Any]] = []
		for target in secondary_targets:
			path = graph.shortest_path(selected_target, target) or graph.shortest_path(target, selected_target)
			if path:
				dependencies.append({"from": selected_target, "to": target, "path": path})
			else:
				dependencies.append({"from": selected_target, "to": target, "path": [selected_target, target]})
		if selected_doc and selected_target:
			dependencies.insert(0, {"from": selected_target, "to": selected_doc, "path": [selected_target, selected_doc]})
		return dependencies
