import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _get_bench_path() -> str:
	try:
		import frappe

		return frappe.utils.get_bench_path()
	except Exception:
		return os.environ.get("FRAPPE_BENCH", os.getcwd())


def get_site_name(site: str | None = None) -> str:
	if site:
		return site

	try:
		import frappe

		if getattr(frappe.local, "site", None):
			return frappe.local.site
	except Exception:
		pass

	return os.environ.get("FRAPPE_SITE", "site1.local")


def get_runtime_paths(site: str | None = None) -> dict[str, str]:
	bench_path = _get_bench_path()
	site_name = get_site_name(site)
	root = Path(bench_path) / "sites" / site_name / "private" / "openclaw"
	home = root / "home"
	config_root = home / ".openclaw"
	workspace = root / "workspace"
	skills_dir = workspace / "skills"
	manifest_dir = root / "manifest"
	log_dir = Path(bench_path) / "logs" / "openclaw"
	app_plugin_dir = Path(bench_path) / "apps" / "mcp_ui" / "openclaw_runtime" / "plugins" / "frappe-federated"

	return {
		"bench_path": bench_path,
		"site": site_name,
		"root": str(root),
		"home": str(home),
		"config_root": str(config_root),
		"config_file": str(config_root / "openclaw.json"),
		"workspace": str(workspace),
		"skills_dir": str(skills_dir),
		"manifest_dir": str(manifest_dir),
		"manifest_file": str(manifest_dir / "current.json"),
		"previous_manifest_file": str(manifest_dir / "previous.json"),
		"manifest_diff_file": str(manifest_dir / "last_diff.json"),
		"state_file": str(root / "runtime_state.json"),
		"session_state_file": str(root / "session_state.json"),
		"pid_file": str(root / "openclaw.pid"),
		"heartbeat_file": str(root / "heartbeat.json"),
		"log_dir": str(log_dir),
		"log_file": str(log_dir / f"{site_name}.log"),
		"plugin_dir": str(root / "plugins"),
		"app_plugin_dir": str(app_plugin_dir),
	}


def ensure_runtime_dirs(site: str | None = None) -> dict[str, str]:
	paths = get_runtime_paths(site)
	for key in (
		"root",
		"home",
		"config_root",
		"workspace",
		"skills_dir",
		"manifest_dir",
		"log_dir",
		"plugin_dir",
	):
		Path(paths[key]).mkdir(parents=True, exist_ok=True)
	return paths


def read_json(path: str, default: Any = None) -> Any:
	try:
		with open(path) as handle:
			return json.load(handle)
	except Exception:
		return default


def write_json(path: str, data: Any) -> None:
	Path(path).parent.mkdir(parents=True, exist_ok=True)
	with open(path, "w") as handle:
		json.dump(_normalize_jsonish(data), handle, indent=2, sort_keys=True, default=str)
		handle.write("\n")


def _normalize_jsonish(value: Any) -> Any:
	if isinstance(value, dict):
		return {str(key): _normalize_jsonish(val) for key, val in value.items()}
	if isinstance(value, (list, tuple, set)):
		return [_normalize_jsonish(item) for item in value]
	return value


def compute_hash(data: Any) -> str:
	payload = json.dumps(_normalize_jsonish(data), sort_keys=True, default=str).encode()
	return hashlib.sha256(payload).hexdigest()


def write_runtime_state(site: str | None = None, **state) -> dict[str, Any]:
	paths = ensure_runtime_dirs(site)
	current = read_json(paths["state_file"], {}) or {}
	current.update(state)
	write_json(paths["state_file"], current)
	return current


def get_session_state(site: str | None = None, session_key: str | None = None) -> dict[str, Any]:
	paths = ensure_runtime_dirs(site)
	store = read_json(paths["session_state_file"], {}) or {}
	if not session_key:
		return store
	return store.get(session_key, {}) or {}


def write_session_state(site: str | None = None, session_key: str | None = None, **state) -> dict[str, Any]:
	if not session_key:
		raise ValueError("session_key is required to write session state")
	paths = ensure_runtime_dirs(site)
	store = read_json(paths["session_state_file"], {}) or {}
	current = store.get(session_key, {}) or {}
	current.update(state)
	store[session_key] = current
	write_json(paths["session_state_file"], store)
	return current
