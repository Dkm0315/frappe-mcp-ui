"""Semantic registry and candidate generation layer."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any

import frappe

from mcp_ui.intent_layer.models.context import ContextResolution
from mcp_ui.intent_layer.models.semantic import SemanticCandidate, SemanticRegistry, SemanticResult
from mcp_ui.intent_layer.utils.cache import cache_get, cache_set
from mcp_ui.intent_layer.utils.graph import RelationshipGraph

try:
	import faiss
except Exception:
	faiss = None

try:
	import numpy as np
except Exception:
	np = None


VECTOR_DIMENSION = 256


class SemanticEngine:
	"""Build schema truth from Frappe metadata and generate semantic candidates."""

	REGISTRY_CACHE_KEY = "semantic_registry"
	FAISS_INDEX_FILE = "intent_layer_faiss.index"
	FAISS_MAP_FILE = "intent_layer_faiss_map.json"
	REGISTRY_FILE = "intent_layer_semantic_registry.json"

	def refresh_registry(self) -> SemanticRegistry:
		site = frappe.local.site
		doctypes = frappe.get_all(
			"DocType",
			filters={"istable": 0},
			fields=["name", "module", "custom", "description", "is_submittable"],
			order_by="name asc",
		)

		fields: dict[str, list[dict[str, Any]]] = {}
		relationships: dict[str, list[dict[str, Any]]] = {}
		workflows: dict[str, dict[str, Any]] = {}
		permissions: dict[str, list[dict[str, Any]]] = {}
		aliases: dict[str, str] = {}
		samples: dict[str, list[dict[str, Any]]] = {}
		doctype_map: dict[str, dict[str, Any]] = {}

		for row in doctypes:
			doctype = row.name
			meta = frappe.get_meta(doctype)
			doctype_map[doctype] = {
				"name": doctype,
				"module": row.module,
				"is_custom": bool(row.custom),
				"description": row.description or "",
				"is_submittable": bool(row.is_submittable),
				"title_field": meta.title_field or "name",
				"search_fields": meta.search_fields or "",
			}
			aliases[_normalize_text(doctype)] = doctype
			aliases[_normalize_text(row.module or "")] = doctype
			if row.description:
				aliases[_normalize_text(row.description)] = doctype

			fields[doctype] = []
			relationships[doctype] = []
			for field in meta.fields:
				field_row = {
					"doctype": doctype,
					"fieldname": field.fieldname,
					"label": field.label or field.fieldname,
					"fieldtype": field.fieldtype,
					"required": bool(field.reqd),
					"options": field.options or "",
					"depends_on": field.depends_on or "",
					"hidden": bool(field.hidden),
				}
				fields[doctype].append(field_row)
				aliases[_normalize_text(field_row["label"])] = doctype
				aliases[_normalize_text(field.fieldname)] = doctype
				if field.fieldtype == "Select" and field.options:
					for option in str(field.options).split("\n"):
						option = option.strip()
						if option:
							aliases[_normalize_text(option)] = doctype

				if field.fieldtype == "Link" and field.options:
					relationships[doctype].append(
						{
							"source_doctype": doctype,
							"target_doctype": field.options,
							"relation_type": "link",
							"fieldname": field.fieldname,
						}
					)
				elif field.fieldtype == "Table" and field.options:
					relationships[doctype].append(
						{
							"source_doctype": doctype,
							"target_doctype": field.options,
							"relation_type": "child_table",
							"fieldname": field.fieldname,
						}
					)

			permissions[doctype] = [
				{
					"role": perm.role,
					"read": bool(perm.read),
					"write": bool(perm.write),
					"create": bool(perm.create),
					"delete": bool(perm.delete),
					"submit": bool(perm.submit),
				}
				for perm in meta.permissions
			]

			workflow_name = frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1}, "name")
			if workflow_name:
				workflow_doc = frappe.get_doc("Workflow", workflow_name)
				workflows[doctype] = {
					"name": workflow_doc.name,
					"workflow_state_field": workflow_doc.workflow_state_field or "workflow_state",
					"states": [
						{
							"state": state.state,
							"doc_status": state.doc_status,
							"allow_edit": state.allow_edit,
						}
						for state in workflow_doc.states
					],
					"transitions": [
						{
							"state": transition.state,
							"action": transition.action,
							"next_state": transition.next_state,
							"allowed": transition.allowed,
						}
						for transition in workflow_doc.transitions
					],
				}
				for state in workflow_doc.states:
					aliases[_normalize_text(state.state)] = doctype
				for transition in workflow_doc.transitions:
					aliases[_normalize_text(transition.action)] = doctype

			samples[doctype] = self._sample_rows(doctype, fields[doctype])

		graph = RelationshipGraph.from_relationships(relationships)
		registry = SemanticRegistry(
			site=site,
			doctypes=doctype_map,
			fields=fields,
			relationships=relationships,
			workflows=workflows,
			permissions=permissions,
			aliases=aliases,
			samples=samples,
			graph=graph.adjacency,
			refreshed_at=str(frappe.utils.now_datetime()),
		)
		registry.checksum = self._checksum_registry(registry.to_dict())
		self._build_vector_index(registry)
		self._persist_registry(registry)
		cache_set(self.REGISTRY_CACHE_KEY, registry.to_dict(), expires_in_sec=3600)
		return registry

	def load_registry(self, force_refresh: bool = False) -> SemanticRegistry:
		if not force_refresh:
			cached = cache_get(self.REGISTRY_CACHE_KEY)
			if cached:
				return SemanticRegistry.from_dict(cached)

		settings = frappe.get_single("MCP Settings")
		registry_path = settings.get("intent_layer_registry_path")
		if not force_refresh and registry_path and os.path.exists(registry_path):
			try:
				payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
				registry = SemanticRegistry.from_dict(payload)
				cache_set(self.REGISTRY_CACHE_KEY, registry.to_dict(), expires_in_sec=3600)
				return registry
			except Exception:
				pass
		return self.refresh_registry()

	def analyze(self, context_payload: dict[str, Any]) -> SemanticResult:
		context = ContextResolution.from_dict(context_payload)
		registry = self.load_registry()
		candidates = self._rank_candidates(context, registry)
		confidence = candidates[0].score if candidates else 0.0
		return SemanticResult(
			intent=context.intent.to_dict(),
			context=context.to_dict(),
			candidates=candidates,
			registry=registry,
			confidence=confidence,
		)

	def _sample_rows(self, doctype: str, doctype_fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
		fields = ["name"]
		for row in doctype_fields:
			if row["fieldtype"] in {"Data", "Link", "Select", "Date", "Datetime"} and not row.get("hidden"):
				fields.append(row["fieldname"])
			if len(fields) >= 6:
				break
		try:
			return frappe.get_all(
				doctype,
				fields=list(dict.fromkeys(fields)),
				order_by="modified desc",
				limit=3,
			)
		except Exception:
			return []

	def _rank_candidates(
		self,
		context: ContextResolution,
		registry: SemanticRegistry,
	) -> list[SemanticCandidate]:
		scores: dict[str, float] = {}
		query_parts = list(context.intent.target_candidates or [])
		if context.resolved_target:
			query_parts.append(context.resolved_target)
		for value in context.intent.entities.values():
			if isinstance(value, str) and value:
				query_parts.append(value)
		if not query_parts:
			query_parts = [context.intent.action]
		query = " ".join(query_parts)

		vector_hits = self._vector_search(query, registry)
		for doctype, score in vector_hits.items():
			scores[doctype] = max(scores.get(doctype, 0.0), score)

		for term in query_parts:
			normalized = _normalize_text(str(term))
			if normalized in registry.aliases:
				doctype = registry.aliases[normalized]
				scores[doctype] = max(scores.get(doctype, 0.0), 0.95)
			for doctype in registry.doctypes:
				score = _lexical_score(normalized, _normalize_text(doctype))
				if score > 0.2:
					scores[doctype] = max(scores.get(doctype, 0.0), score)

		if context.resolved_target and context.resolved_target in registry.doctypes:
			scores[context.resolved_target] = max(scores.get(context.resolved_target, 0.0), 0.98)

		candidates = [
			SemanticCandidate(
				doctype=doctype,
				score=round(score, 4),
				fields={
					row["fieldname"]: row
					for row in registry.fields.get(doctype, [])
				},
				workflow=registry.workflows.get(doctype, {}),
				permissions=registry.permissions.get(doctype, []),
				relationships=registry.relationships.get(doctype, []),
			)
			for doctype, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
			if score >= 0.15
		]
		return candidates[:8]

	def _build_vector_index(self, registry: SemanticRegistry) -> None:
		registry_dir = Path(frappe.get_site_path("private", "files", "intent_layer"))
		registry_dir.mkdir(parents=True, exist_ok=True)
		index_path = registry_dir / self.FAISS_INDEX_FILE
		map_path = registry_dir / self.FAISS_MAP_FILE
		records: list[dict[str, Any]] = []
		vectors: list[list[float]] = []

		for doctype, meta in registry.doctypes.items():
			text = " ".join(
				[
					doctype,
					meta.get("description") or "",
					meta.get("module") or "",
					" ".join(
						f"{row.get('label') or ''} {row.get('fieldname') or ''} {row.get('options') or ''}"
						for row in registry.fields.get(doctype, [])[:20]
					),
				]
			)
			records.append({"vector_id": len(records), "doctype": doctype, "text": text[:2000]})
			vectors.append(_text_vector(text))

		map_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
		registry.faiss_map_path = str(map_path)
		registry.faiss_path = ""

		if faiss is None or np is None or not vectors:
			return

		matrix = np.array(vectors, dtype="float32")
		index = faiss.IndexFlatIP(VECTOR_DIMENSION)
		index.add(matrix)
		faiss.write_index(index, str(index_path))
		registry.faiss_path = str(index_path)

	def _vector_search(self, query: str, registry: SemanticRegistry) -> dict[str, float]:
		if not query:
			return {}
		vector = _text_vector(query)
		map_path = registry.faiss_map_path
		if faiss is None or np is None or not registry.faiss_path or not map_path:
			return self._lexical_map_search(vector, query, map_path)
		try:
			index = faiss.read_index(registry.faiss_path)
			query_matrix = np.array([vector], dtype="float32")
			scores, indexes = index.search(query_matrix, min(10, index.ntotal))
			records = {
				int(row["vector_id"]): row
				for row in json.loads(Path(map_path).read_text(encoding="utf-8"))
			}
			hits: dict[str, float] = {}
			for raw_score, vector_id in zip(scores[0].tolist(), indexes[0].tolist(), strict=False):
				if vector_id < 0 or vector_id not in records:
					continue
				doctype = records[vector_id]["doctype"]
				hits[doctype] = max(hits.get(doctype, 0.0), float(raw_score))
			return hits
		except Exception:
			return self._lexical_map_search(vector, query, map_path)

	def _lexical_map_search(
		self,
		vector: list[float],
		query: str,
		map_path: str,
	) -> dict[str, float]:
		_ = vector
		if not map_path or not os.path.exists(map_path):
			return {}
		hits: dict[str, float] = {}
		try:
			records = json.loads(Path(map_path).read_text(encoding="utf-8"))
		except Exception:
			return {}
		normalized_query = _normalize_text(query)
		for row in records:
			doctype = row.get("doctype")
			score = _lexical_score(normalized_query, _normalize_text(row.get("text") or ""))
			if doctype and score > 0.1:
				hits[doctype] = max(hits.get(doctype, 0.0), score)
		return hits

	def _persist_registry(self, registry: SemanticRegistry) -> None:
		registry_dir = Path(frappe.get_site_path("private", "files", "intent_layer"))
		registry_dir.mkdir(parents=True, exist_ok=True)
		registry_path = registry_dir / self.REGISTRY_FILE
		registry_path.write_text(json.dumps(registry.to_dict(), indent=2, default=str), encoding="utf-8")

		settings = frappe.get_single("MCP Settings")
		settings.intent_layer_registry_path = str(registry_path)
		settings.intent_layer_faiss_path = registry.faiss_path
		settings.intent_layer_faiss_map_path = registry.faiss_map_path
		settings.intent_layer_last_refresh = registry.refreshed_at
		settings.intent_layer_schema_checksum = registry.checksum
		settings.intent_layer_vector_backend = "FAISS Local" if registry.faiss_path else "Lexical Fallback"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _checksum_registry(self, payload: dict[str, Any]) -> str:
		raw = json.dumps(payload, sort_keys=True, default=str)
		return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize_text(value: str) -> str:
	return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()


def _lexical_score(query: str, candidate: str) -> float:
	query = _normalize_text(query)
	candidate = _normalize_text(candidate)
	if not query or not candidate:
		return 0.0
	if query == candidate:
		return 1.0
	if query in candidate:
		return min(0.95, 0.6 + len(query) / max(len(candidate), 1))
	query_tokens = set(query.split())
	candidate_tokens = set(candidate.split())
	if not query_tokens or not candidate_tokens:
		return 0.0
	overlap = len(query_tokens & candidate_tokens)
	union = len(query_tokens | candidate_tokens)
	return overlap / union


def _text_vector(text: str) -> list[float]:
	vector = [0.0] * VECTOR_DIMENSION
	for token in _normalize_text(text).split():
		digest = hashlib.sha256(token.encode("utf-8")).digest()
		idx = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSION
		sign = -1.0 if digest[4] % 2 else 1.0
		vector[idx] += sign
	norm = math.sqrt(sum(value * value for value in vector)) or 1.0
	return [value / norm for value in vector]
