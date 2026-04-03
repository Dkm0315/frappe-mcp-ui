"""Intent extraction layer using the existing AI provider config."""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
import litellm

from mcp_ui.ai.providers import get_provider_config
from mcp_ui.intent_layer.models.intent import IntentPayload
from mcp_ui.intent_layer.utils.prompts import INTENT_EXTRACTION_PROMPT


ACTION_SYNONYMS = {
	"add": "create",
	"make": "create",
	"new": "create",
	"create": "create",
	"show": "read",
	"get": "read",
	"fetch": "read",
	"view": "read",
	"who": "list",
	"which": "list",
	"what": "read",
	"where": "search",
	"find": "search",
	"lookup": "search",
	"search": "search",
	"list": "list",
	"modify": "update",
	"edit": "update",
	"change": "update",
	"assign": "update",
	"resolve": "update",
	"remove": "delete",
	"discard": "delete",
	"close": "workflow",
	"start": "workflow",
	"approve": "workflow",
	"reject": "workflow",
	"transition": "workflow",
	"submit": "submit",
	"cancel": "cancel",
	"pay": "pay",
	"update": "update",
	"delete": "delete",
	"notify": "notify",
	"message": "notify",
	"send": "notify",
}

AMBIGUOUS_HINTS = {"invoice", "invoices", "issue", "issues", "job", "jobs", "order", "orders", "leave"}

TARGET_HINTS: dict[str, list[str]] = {
	"customer": ["Customer"],
	"customers": ["Customer"],
	"invoice": ["Sales Invoice", "Purchase Invoice", "POS Invoice"],
	"invoices": ["Sales Invoice", "Purchase Invoice", "POS Invoice"],
	"sales invoice": ["Sales Invoice"],
	"sales invoices": ["Sales Invoice"],
	"purchase invoice": ["Purchase Invoice"],
	"purchase invoices": ["Purchase Invoice"],
	"payment": ["Payment Entry"],
	"payments": ["Payment Entry"],
	"payment entry": ["Payment Entry"],
	"payment entries": ["Payment Entry"],
	"order": ["Sales Order", "Purchase Order", "Work Order"],
	"orders": ["Sales Order", "Purchase Order", "Work Order"],
	"sales order": ["Sales Order"],
	"sales orders": ["Sales Order"],
	"supplier": ["Supplier"],
	"suppliers": ["Supplier"],
	"item": ["Item"],
	"items": ["Item"],
	"lead": ["Lead"],
	"leads": ["Lead"],
	"quotation": ["Quotation"],
	"quotations": ["Quotation"],
	"ticket": ["HD Ticket", "Issue"],
	"tickets": ["HD Ticket", "Issue"],
	"helpdesk ticket": ["HD Ticket"],
	"issue": ["Issue", "Stock Entry"],
	"issues": ["Issue"],
	"shop floor job": ["Job Card", "Work Order"],
	"job card": ["Job Card"],
	"work order": ["Work Order"],
	"production": ["Production Plan", "Work Order", "Job Card"],
	"pump batch": ["Work Order", "Batch", "Production Plan"],
	"raw material": ["Stock Entry", "Work Order", "Job Card"],
	"qc": ["Quality Inspection", "Quality Review"],
	"qc check": ["Quality Inspection"],
	"qc hold": ["Quality Review", "Quality Inspection"],
	"operator": ["Employee", "Shift Assignment"],
	"operators": ["Employee", "Shift Assignment"],
	"leave": ["Leave Application", "Attendance"],
	"off": ["Leave Application", "Attendance"],
	"shift": ["Shift Assignment", "Shift Type"],
	"comp off": ["Compensatory Leave Request", "Leave Application"],
	"comp-off": ["Compensatory Leave Request", "Leave Application"],
	"overtime": ["Additional Salary", "Attendance Request"],
	"welder": ["Employee", "Shift Assignment"],
	"telegram": ["Telegram Message", "Telegram Chat", "Telegram User"],
	"message": ["Telegram Message", "Communication"],
	"dispatch": ["Delivery Note", "Shipment"],
}

STOP_WORDS = {
	"a",
	"an",
	"and",
	"are",
	"all",
	"anyway",
	"be",
	"can",
	"did",
	"do",
	"for",
	"from",
	"how",
	"in",
	"is",
	"latest",
	"lol",
	"mark",
	"me",
	"of",
	"on",
	"our",
	"paid",
	"s",
	"the",
	"thing",
	"to",
	"with",
	"that",
	"this",
	"those",
	"these",
	"please",
	"who",
	"which",
	"what",
	"where",
	"why",
	"yesterday",
	"today",
	"tomorrow",
	"week",
	"without",
	"last",
	"submitting",
}

LEADING_ENTITY_NOISE = (
	"who are",
	"which are",
	"what are",
	"show me",
	"can you",
	"please",
)


class IntentEngine:
	"""Convert natural-language text into the strict intent JSON contract."""

	def parse(self, message: str) -> IntentPayload:
		message = (message or "").strip()
		if not message:
			return IntentPayload(action="unknown", ambiguity=True, missing_fields=["message"])

		llm_payload = self._parse_with_llm(message)
		payload = llm_payload or self._parse_with_rules(message)
		intent = IntentPayload.from_dict(payload)
		intent.action = ACTION_SYNONYMS.get(intent.action.lower(), intent.action.lower() or "unknown")
		if not intent.target_candidates:
			intent.target_candidates = self._extract_target_candidates(message)
		if intent.action == "unknown":
			intent.ambiguity = True
		if intent.action == "create" and not intent.entities:
			intent.entities = self._extract_entities(message, intent.target_candidates)
		if not intent.missing_fields and intent.action == "create" and not intent.entities:
			intent.missing_fields = ["data"]
		return intent

	def _parse_with_llm(self, message: str) -> dict[str, Any] | None:
		config = get_provider_config()
		if not config.get("enabled") or not config.get("model"):
			return None

		llm_kwargs = {"model": config["model"]}
		if config.get("api_key"):
			llm_kwargs["api_key"] = config["api_key"]
		if config.get("api_base"):
			llm_kwargs["api_base"] = config["api_base"]

		try:
			response = litellm.completion(
				messages=[
					{
						"role": "user",
						"content": INTENT_EXTRACTION_PROMPT.format(message=message),
					}
				],
				temperature=0,
				**llm_kwargs,
			)
			content = response.choices[0].message.content if response and response.choices else ""
			return _safe_json_object(content)
		except Exception as exc:
			frappe.logger("intent_layer").warning(f"Intent LLM fallback activated: {exc}")
			return None

	def _parse_with_rules(self, message: str) -> dict[str, Any]:
		lowered = message.lower().strip()
		action = "unknown"
		if re.match(r"^(who|which)\b", lowered):
			action = "list"
		elif re.match(r"^(what|show|get|view)\b", lowered):
			action = "read"
		elif re.search(r"\bstart\s+(production|work|job|batch)\b", lowered):
			action = "workflow"
		elif re.search(r"\b(close|approve|reject)\b", lowered):
			action = "workflow"
		elif re.search(r"\b(issue|assign)\b", lowered):
			action = "update"
		elif re.search(r"\b(send|message|notify)\b", lowered):
			action = "notify"
		for token, canonical in ACTION_SYNONYMS.items():
			if action != "unknown":
				break
			if re.search(rf"\b{re.escape(token)}\b", lowered):
				action = canonical
				break
		target_candidates = self._extract_target_candidates(message)
		entities = self._extract_entities(message, target_candidates)
		if "payment" in lowered and "Payment Entry" not in target_candidates:
			entities.setdefault("secondary_targets", []).append("Payment Entry")
		if re.search(r"\bthat\s+\w+|\bthis\s+\w+|\bit\b", lowered):
			entities.setdefault("context_reference", "that")
		return {
			"action": action,
			"target_candidates": target_candidates,
			"entities": entities,
			"confidence": 0.72 if action != "unknown" else 0.2,
			"ambiguity": action == "unknown" or len(target_candidates) > 1 or _has_ambiguous_hint(lowered),
			"missing_fields": [],
		}

	def _extract_target_candidates(self, message: str) -> list[str]:
		lowered = message.lower()
		candidates: list[str] = []
		if re.search(r"\b(last\s+send|last\s+sent|last\s+message|what\s+did\s+we\s+last\s+send)\b", lowered):
			candidates.extend(["Communication", "Telegram Message"])
		for hint, doctypes in sorted(TARGET_HINTS.items(), key=lambda item: len(item[0]), reverse=True):
			if not re.search(rf"\b{re.escape(hint)}\b", lowered):
				continue
			for doctype in doctypes:
				if doctype not in candidates:
					candidates.append(doctype)
		if candidates:
			return candidates

		words = []
		for word in re.findall(r"[a-zA-Z][\w-]*", message):
			lowered_word = word.lower()
			if lowered_word in STOP_WORDS or lowered_word in ACTION_SYNONYMS:
				continue
			words.append(_singularize(word))
		if not words:
			return []
		if len(words) >= 2:
			candidates.append(" ".join(words[:2]).title())
		elif words:
			candidates.append(words[0].title())
		return candidates

	def _extract_entities(self, message: str, target_candidates: list[str]) -> dict[str, Any]:
		entities: dict[str, Any] = {}
		lowered = message.lower()
		for match in re.finditer(r"\b([a-zA-Z_][\w ]{0,32})\s*=\s*([^\s,]+)", message):
			entities[match.group(1).strip()] = match.group(2).strip().strip("\"'")

		if "customer" in lowered:
			match = re.search(r"\bcustomer\s+([a-zA-Z0-9 _-]+)$", message, flags=re.I)
			if match:
				value = match.group(1).strip()
				if value.lower() not in {"that customer", "this customer"}:
					entities["customer_name"] = value

		if target_candidates:
			entity_tail = re.sub(
				r"^(create|add|make|new|show|get|fetch|view|find|lookup|modify|edit|change|remove|discard|submit|cancel|pay|list|search|who|which|what|where|start|close|assign|issue|message|notify|send)\b",
				"",
				message,
				flags=re.I,
			).strip()
			for doctype in target_candidates:
				entity_tail = re.sub(re.escape(doctype), "", entity_tail, flags=re.I).strip()
				for token in doctype.split():
					entity_tail = re.sub(rf"\b{re.escape(token)}\b", "", entity_tail, flags=re.I).strip()
					entity_tail = re.sub(rf"\b{re.escape(token)}s\b", "", entity_tail, flags=re.I).strip()
					entity_tail = re.sub(rf"\b{re.escape(_singularize(token))}\b", "", entity_tail, flags=re.I).strip()
				for hint, hint_doctypes in TARGET_HINTS.items():
					if doctype in hint_doctypes:
						entity_tail = re.sub(rf"\b{re.escape(hint)}\b", "", entity_tail, flags=re.I).strip()
			for prefix in LEADING_ENTITY_NOISE:
				entity_tail = re.sub(rf"^{re.escape(prefix)}\b", "", entity_tail, flags=re.I).strip()
			entity_tail = " ".join(word for word in entity_tail.split() if word.lower() not in STOP_WORDS)
			entity_tail = re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", entity_tail).strip()
			if _is_meaningful_entity_tail(entity_tail) and "name" not in entities:
				entities["name"] = entity_tail
		return entities


def _safe_json_object(content: str | None) -> dict[str, Any] | None:
	if not content:
		return None
	candidate = content.strip()
	if candidate.startswith("```"):
		candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
		candidate = re.sub(r"```$", "", candidate).strip()
	try:
		payload = json.loads(candidate)
		if isinstance(payload, dict):
			return payload
	except Exception:
		match = re.search(r"\{.*\}", candidate, flags=re.S)
		if match:
			try:
				payload = json.loads(match.group(0))
				if isinstance(payload, dict):
					return payload
			except Exception:
				return None
	return None


def _singularize(word: str) -> str:
	value = (word or "").lower()
	if value.endswith("ies") and len(value) > 3:
		return f"{value[:-3]}y"
	if value.endswith(("ses", "xes", "zes", "ches", "shes")) and len(value) > 2:
		return value[:-2]
	if value.endswith("s") and not value.endswith("ss") and len(value) > 1:
		return value[:-1]
	return value


def _has_ambiguous_hint(message: str) -> bool:
	if "purchase invoice" in message or "sales invoice" in message or "pos invoice" in message:
		return False
	for hint in AMBIGUOUS_HINTS:
		if re.search(rf"\b{re.escape(hint)}\b", message):
			return True
	return False


def _is_meaningful_entity_tail(value: str) -> bool:
	normalized = re.sub(r"[^a-zA-Z0-9]+", "", value or "")
	if len(normalized) <= 2:
		return False
	if normalized.lower() in STOP_WORDS:
		return False
	return True
