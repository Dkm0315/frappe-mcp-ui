"""Customization registry model."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CustomizationRegistry:
	site: str
	custom_doctypes: dict[str, dict[str, Any]] = field(default_factory=dict)
	custom_fields: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
	controllers: dict[str, dict[str, Any]] = field(default_factory=dict)
	hooks: dict[str, Any] = field(default_factory=dict)
	server_scripts: list[dict[str, Any]] = field(default_factory=list)
	client_scripts: list[dict[str, Any]] = field(default_factory=list)
	api_map: dict[str, dict[str, Any]] = field(default_factory=dict)
	ui_routes: list[dict[str, Any]] = field(default_factory=list)
	behavior_graph: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
	rule_set: list[dict[str, Any]] = field(default_factory=list)
	refreshed_at: str = ""
	checksum: str = ""

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)

	@classmethod
	def from_dict(cls, payload: dict[str, Any] | None) -> "CustomizationRegistry":
		payload = payload or {}
		return cls(
			site=str(payload.get("site") or ""),
			custom_doctypes=dict(payload.get("custom_doctypes") or {}),
			custom_fields=dict(payload.get("custom_fields") or {}),
			controllers=dict(payload.get("controllers") or {}),
			hooks=dict(payload.get("hooks") or {}),
			server_scripts=list(payload.get("server_scripts") or []),
			client_scripts=list(payload.get("client_scripts") or []),
			api_map=dict(payload.get("api_map") or {}),
			ui_routes=list(payload.get("ui_routes") or []),
			behavior_graph=dict(payload.get("behavior_graph") or {}),
			rule_set=list(payload.get("rule_set") or []),
			refreshed_at=str(payload.get("refreshed_at") or ""),
			checksum=str(payload.get("checksum") or ""),
		)
