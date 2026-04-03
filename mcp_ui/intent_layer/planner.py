"""Planner that enforces API > workflow > CRUD priority."""

from __future__ import annotations

from typing import Any

import frappe

from mcp_ui.intent_layer.models.plan import PlanEnvelope, PlanStep


class Planner:
	"""Generate ordered deterministic plans from validated reasoning output."""

	def build(
		self,
		intent_payload: dict[str, Any],
		context_payload: dict[str, Any],
		semantic_payload: dict[str, Any],
		customization_payload: dict[str, Any],
		reasoning_payload: dict[str, Any],
		user_id: str,
	) -> PlanEnvelope:
		plan_id = frappe.generate_hash(length=12)
		steps: list[PlanStep] = []
		target = reasoning_payload.get("selected_target") or context_payload.get("resolved_target") or ""
		selected_doc = reasoning_payload.get("selected_doc") or context_payload.get("resolved_doc") or ""
		action = (reasoning_payload.get("action") or intent_payload.get("action") or "unknown").lower()
		entities = dict(reasoning_payload.get("entities") or intent_payload.get("entities") or {})
		preferred_api = dict(reasoning_payload.get("preferred_api") or {})
		workflow = dict(reasoning_payload.get("workflow") or {})
		secondary_targets = list(reasoning_payload.get("secondary_targets") or [])

		if action == "unknown" or not target or reasoning_payload.get("ambiguity"):
			return PlanEnvelope(
				plan_id=plan_id,
				intent=intent_payload,
				context=context_payload,
				semantic=self._semantic_summary(semantic_payload),
				customization=self._customization_summary(customization_payload, reasoning_payload),
				reasoning=reasoning_payload,
				steps=[],
				status="failed",
			)

		if preferred_api:
			steps.append(
				PlanStep(
					step_id="step-1",
					action="custom_api",
					target=target or preferred_api.get("doctype") or "",
					tool="call_custom_api",
					input={
						"method": preferred_api.get("method"),
						"params": self._api_params(action, target, selected_doc, entities),
						"user_id": user_id,
					},
					idempotent=action not in {"create", "delete"},
					sensitive=action in {"delete", "pay"},
				)
			)
			return PlanEnvelope(
				plan_id=plan_id,
				intent=intent_payload,
				context=context_payload,
				semantic=self._semantic_summary(semantic_payload),
				customization=self._customization_summary(customization_payload, reasoning_payload),
				reasoning=reasoning_payload,
				steps=steps,
				status="pending",
			)

		if workflow and action in {"workflow", "submit", "approve", "reject", "pay"} and selected_doc:
			workflow_action = entities.get("workflow_action") or entities.get("action") or ""
			if not workflow_action:
				workflow_action = self._infer_workflow_action(workflow, action)
			steps.append(
				PlanStep(
					step_id="step-1",
					action="workflow",
					target=target,
					tool="apply_workflow" if workflow_action else "submit_doc",
					input={
						"doctype": target,
						"name": selected_doc,
						"action": workflow_action,
						"user_id": user_id,
					}
					if workflow_action
					else {
						"doctype": target,
						"name": selected_doc,
						"user_id": user_id,
					},
					idempotent=False,
					sensitive=action in {"pay", "approve", "reject"},
				)
			)
			return PlanEnvelope(
				plan_id=plan_id,
				intent=intent_payload,
				context=context_payload,
				semantic=self._semantic_summary(semantic_payload),
				customization=self._customization_summary(customization_payload, reasoning_payload),
				reasoning=reasoning_payload,
				steps=steps,
				status="pending",
			)

		steps.extend(self._crud_steps(action, target, selected_doc, entities, user_id))
		if action == "create" and secondary_targets:
			steps.extend(self._secondary_create_steps(steps, secondary_targets, entities, user_id))

		return PlanEnvelope(
			plan_id=plan_id,
			intent=intent_payload,
			context=context_payload,
			semantic=self._semantic_summary(semantic_payload),
			customization=self._customization_summary(customization_payload, reasoning_payload),
			reasoning=reasoning_payload,
			steps=steps,
			status="pending" if steps else "failed",
		)

	def _crud_steps(
		self,
		action: str,
		target: str,
		selected_doc: str,
		entities: dict[str, Any],
		user_id: str,
	) -> list[PlanStep]:
		if not target:
			return []
		if action == "create":
			data = self._create_payload(target, entities)
			return [
				PlanStep(
					step_id="step-1",
					action="create",
					target=target,
					tool="create_doc",
					input={"doctype": target, "data": data, "user_id": user_id},
					idempotent=False,
				)
			]
		if action == "update" and selected_doc:
			return [
				PlanStep(
					step_id="step-1",
					action="update",
					target=target,
					tool="update_doc",
					input={
						"doctype": target,
						"name": selected_doc,
						"data": self._update_payload(entities),
						"user_id": user_id,
					},
					idempotent=True,
				)
			]
		if action == "delete" and selected_doc:
			return [
				PlanStep(
					step_id="step-1",
					action="delete",
					target=target,
					tool="delete_doc",
					input={"doctype": target, "name": selected_doc, "confirm": False, "user_id": user_id},
					idempotent=False,
					sensitive=True,
				)
			]
		if action in {"read", "get"} and selected_doc:
			return [
				PlanStep(
					step_id="step-1",
					action="read",
					target=target,
					tool="get_doc",
					input={"doctype": target, "name": selected_doc, "user_id": user_id},
				)
			]
		if action == "search":
			return [
				PlanStep(
					step_id="step-1",
					action="search",
					target=target,
					tool="search_docs",
					input={
						"doctype": target,
						"query": entities.get("query") or entities.get("name") or "",
						"user_id": user_id,
					},
				)
			]
		if action in {"list", "read"}:
			return [
				PlanStep(
					step_id="step-1",
					action="list",
					target=target,
					tool="list_docs",
					input={"doctype": target, "limit": 20, "user_id": user_id},
				)
			]
		if action == "pay" and selected_doc:
			return [
				PlanStep(
					step_id="step-1",
					action="read",
					target=target,
					tool="get_doc",
					input={"doctype": target, "name": selected_doc, "user_id": user_id},
					idempotent=True,
				),
				PlanStep(
					step_id="step-2",
					action="create_payment",
					target="Payment Entry",
					tool="create_doc",
					dependencies=["step-1"],
					input={
						"doctype": "Payment Entry",
						"data": {
							"payment_type": "Receive",
							"party_type": "Customer",
							"party": entities.get("customer") or entities.get("customer_name") or "",
							"reference_no": selected_doc,
							"reference_date": frappe.utils.nowdate(),
							"paid_amount": entities.get("paid_amount") or 0,
							"received_amount": entities.get("received_amount") or entities.get("paid_amount") or 0,
						},
						"user_id": user_id,
					},
					idempotent=False,
					sensitive=True,
				),
			]
		return []

	def _secondary_create_steps(
		self,
		existing_steps: list[PlanStep],
		secondary_targets: list[str],
		entities: dict[str, Any],
		user_id: str,
	) -> list[PlanStep]:
		steps: list[PlanStep] = []
		base_dependency = existing_steps[-1].step_id if existing_steps else "step-1"
		for index, target in enumerate(secondary_targets, start=len(existing_steps) + 1):
			steps.append(
				PlanStep(
					step_id=f"step-{index}",
					action="create",
					target=target,
					tool="create_doc",
					dependencies=[base_dependency],
					input={"doctype": target, "data": self._create_payload(target, entities), "user_id": user_id},
					idempotent=False,
					sensitive=target == "Payment Entry",
				)
			)
		return steps

	def _api_params(
		self,
		action: str,
		target: str,
		selected_doc: str,
		entities: dict[str, Any],
	) -> dict[str, Any]:
		params = dict(entities or {})
		params.setdefault("doctype", target)
		params.setdefault("dt", target)
		if selected_doc:
			params.setdefault("name", selected_doc)
			params.setdefault("docname", selected_doc)
		params.setdefault("action", action)
		return params

	def _create_payload(self, target: str, entities: dict[str, Any]) -> dict[str, Any]:
		payload = {
			key: value
			for key, value in entities.items()
			if key
			not in {
				"context_reference",
				"secondary_targets",
				"doctype",
				"document_name",
				"workflow_action",
				"action",
			}
		}
		if target == "Customer":
			customer_name = payload.pop("customer_name", None) or payload.pop("name", None)
			if customer_name:
				payload.setdefault("customer_name", customer_name)
				payload.setdefault("customer_type", "Individual")
		if target == "Supplier":
			supplier_name = payload.pop("supplier_name", None) or payload.pop("name", None)
			if supplier_name:
				payload.setdefault("supplier_name", supplier_name)
				payload.setdefault("supplier_type", "Individual")
		if target == "Sales Invoice":
			if payload.get("customer_name") and not payload.get("customer"):
				payload["customer"] = payload.pop("customer_name")
		return payload

	def _update_payload(self, entities: dict[str, Any]) -> dict[str, Any]:
		payload = self._create_payload("", entities)
		payload.pop("name", None)
		return payload

	def _infer_workflow_action(self, workflow: dict[str, Any], action: str) -> str:
		for transition in workflow.get("transitions") or []:
			candidate = str(transition.get("action") or "")
			lowered = candidate.lower()
			if action == "pay" and "pay" in lowered:
				return candidate
			if action in {"submit", "workflow"} and lowered in {"submit", "approve"}:
				return candidate
			if action == "approve" and "approve" in lowered:
				return candidate
			if action == "reject" and "reject" in lowered:
				return candidate
		return ""

	def _semantic_summary(self, semantic_payload: dict[str, Any]) -> dict[str, Any]:
		candidates = [
			{
				"doctype": candidate.get("doctype"),
				"score": candidate.get("score"),
			}
			for candidate in (semantic_payload.get("candidates") or [])[:8]
		]
		registry = semantic_payload.get("registry") or {}
		return {
			"confidence": semantic_payload.get("confidence", 0.0),
			"candidate_count": len(semantic_payload.get("candidates") or []),
			"top_candidates": candidates,
			"registry_checksum": registry.get("checksum"),
			"refreshed_at": registry.get("refreshed_at"),
		}

	def _customization_summary(
		self,
		customization_payload: dict[str, Any],
		reasoning_payload: dict[str, Any],
	) -> dict[str, Any]:
		selected_target = reasoning_payload.get("selected_target")
		return {
			"checksum": customization_payload.get("checksum"),
			"refreshed_at": customization_payload.get("refreshed_at"),
			"selected_target": selected_target,
			"preferred_api": reasoning_payload.get("preferred_api") or {},
			"behavior_count": len((customization_payload.get("behavior_graph") or {}).get(selected_target, []))
			if selected_target
			else 0,
			"rule_count": len(customization_payload.get("rule_set") or []),
		}
