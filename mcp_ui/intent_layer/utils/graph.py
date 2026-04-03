"""Simple adjacency graph utilities for vectorless reasoning."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class RelationshipGraph:
	adjacency: dict[str, list[str]] = field(default_factory=dict)

	def add_edge(self, source: str, target: str) -> None:
		if not source or not target:
			return
		self.adjacency.setdefault(source, [])
		if target not in self.adjacency[source]:
			self.adjacency[source].append(target)
		self.adjacency.setdefault(target, [])

	def neighbors(self, node: str) -> list[str]:
		return list(self.adjacency.get(node) or [])

	def shortest_path(self, source: str, target: str, max_depth: int = 4) -> list[str]:
		if not source or not target:
			return []
		if source == target:
			return [source]
		queue = deque([(source, [source])])
		seen = {source}
		while queue:
			node, path = queue.popleft()
			if len(path) > max_depth + 1:
				continue
			for nxt in self.adjacency.get(node) or []:
				if nxt in seen:
					continue
				new_path = [*path, nxt]
				if nxt == target:
					return new_path
				seen.add(nxt)
				queue.append((nxt, new_path))
		return []

	@classmethod
	def from_relationships(cls, relationships: dict[str, list[dict]]) -> "RelationshipGraph":
		graph = cls()
		for source, edges in (relationships or {}).items():
			for edge in edges or []:
				graph.add_edge(source, edge.get("target_doctype"))
		return graph
