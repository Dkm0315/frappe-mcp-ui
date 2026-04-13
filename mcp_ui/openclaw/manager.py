"""
OpenClaw Gateway Process Manager

Runs OpenClaw in a bench-local home/workspace so hosted/global user state is
not mixed across benches or sites. The scheduler acts as a watchdog.
"""
from __future__ import annotations

import os
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import frappe

from mcp_ui.openclaw.runtime import ensure_runtime_dirs, read_json, write_json, write_runtime_state
from mcp_ui.openclaw.site_context import refresh_site_context


def _utcnow() -> str:
	return datetime.now(timezone.utc).isoformat()


def _get_paths() -> dict[str, str]:
	paths = ensure_runtime_dirs(frappe.local.site)
	bench_path = paths["bench_path"]
	app_path = os.path.join(bench_path, "apps", "mcp_ui")
	runtime_dir = os.path.join(app_path, "openclaw_runtime")
	paths.update(
		{
			"app_path": app_path,
			"openclaw_runtime": runtime_dir,
			"openclaw_bin": os.path.join(runtime_dir, "node_modules", ".bin", "openclaw"),
			"openclaw_entry": os.path.join(runtime_dir, "node_modules", "openclaw", "openclaw.mjs"),
		}
	)
	return paths


def _read_pid(pid_file: str) -> int | None:
	try:
		with open(pid_file) as handle:
			return int(handle.read().strip())
	except Exception:
		return None


def _is_running(pid_file: str) -> bool:
	pid = _read_pid(pid_file)
	if not pid:
		return False

	try:
		os.kill(pid, 0)
		return True
	except (ProcessLookupError, PermissionError, OSError):
		try:
			os.unlink(pid_file)
		except OSError:
			pass
		return False


def _is_openclaw_enabled() -> bool:
	try:
		return bool(frappe.db.get_single_value("MCP Settings", "openclaw_enabled"))
	except Exception:
		return False


def _discover_node_binary() -> str | None:
	settings_path = frappe.conf.get("openclaw_node_path")
	candidates = [settings_path, os.environ.get("OPENCLAW_NODE_PATH"), os.environ.get("NVM_BIN") and os.path.join(os.environ["NVM_BIN"], "node")]

	home = os.path.expanduser("~")
	candidates.extend(
		[
			os.path.join(home, ".nvm", "versions", "node", "v24.13.0", "bin", "node"),
			os.path.join(home, ".nvm", "versions", "node", "v22.22.0", "bin", "node"),
			"/opt/homebrew/bin/node",
			"/usr/local/bin/node",
			"node",
		]
	)

	for candidate in candidates:
		if not candidate:
			continue
		try:
			result = subprocess.run(
				[candidate, "--version"],
				check=False,
				capture_output=True,
				text=True,
				timeout=5,
			)
			if result.returncode != 0:
				continue
			version = result.stdout.strip().lstrip("v")
			major = int(version.split(".", 1)[0])
			if major >= 22:
				return candidate
		except Exception:
			continue

	return None


def _is_openclaw_installed(paths: dict) -> bool:
	return os.path.isfile(paths["openclaw_entry"])


def _has_config(paths: dict) -> bool:
	return os.path.isfile(paths["config_file"])


def _sessions_dir(paths: dict) -> Path:
	return Path(paths["home"]) / ".openclaw" / "agents" / "main" / "sessions"


def _pid_alive(pid: int | None) -> bool:
	if not pid:
		return False
	try:
		os.kill(pid, 0)
		return True
	except (ProcessLookupError, PermissionError, OSError):
		return False


def _sanitize_session_store(paths: dict) -> dict[str, int]:
	sessions_dir = _sessions_dir(paths)
	store_path = sessions_dir / "sessions.json"
	config = read_json(paths["config_file"], {}) or {}
	disable_native_skills = config.get("commands", {}).get("nativeSkills") is False
	stats = {"snapshots_cleared": 0, "locks_removed": 0}

	store = read_json(str(store_path), None)
	if isinstance(store, dict):
		changed = False
		for entry in store.values():
			if not isinstance(entry, dict):
				continue
			if disable_native_skills and entry.pop("skillsSnapshot", None) is not None:
				stats["snapshots_cleared"] += 1
				changed = True
		if changed:
			write_json(str(store_path), store)

	for lock_file in sessions_dir.glob("*.jsonl.lock"):
		session_file = Path(str(lock_file)[:-5])
		lock_payload = read_json(str(lock_file), {}) or {}
		lock_pid = None
		try:
			lock_pid = int(lock_payload.get("pid"))
		except Exception:
			lock_pid = None
		if session_file.exists() and _pid_alive(lock_pid):
			continue
		try:
			lock_file.unlink()
			stats["locks_removed"] += 1
		except OSError:
			pass

	return stats


def install_openclaw():
	paths = _get_paths()
	runtime_dir = paths["openclaw_runtime"]
	os.makedirs(runtime_dir, exist_ok=True)

	node_bin = _discover_node_binary()
	if not node_bin:
		return {"success": False, "error": "Node 22+ not found. Configure OPENCLAW_NODE_PATH or install Node 22/24."}

	npm_bin = os.path.join(os.path.dirname(node_bin), "npm")
	if not os.path.exists(npm_bin):
		npm_bin = "npm"

	try:
		result = subprocess.run(
			[npm_bin, "install", "--production"],
			cwd=runtime_dir,
			capture_output=True,
			text=True,
			timeout=180,
		)
		if result.returncode == 0:
			frappe.logger("openclaw").info("OpenClaw npm packages installed successfully")
			return {"success": True, "output": result.stdout, "node": node_bin}
		frappe.logger("openclaw").error(f"npm install failed: {result.stderr}")
		return {"success": False, "error": result.stderr, "node": node_bin}
	except FileNotFoundError:
		return {"success": False, "error": "npm not found. Install Node.js first."}
	except subprocess.TimeoutExpired:
		return {"success": False, "error": "npm install timed out after 180s"}


def _build_gateway_env(settings, paths: dict) -> dict[str, str]:
	env = os.environ.copy()
	env["HOME"] = paths["home"]
	env["FRAPPE_SITE"] = paths["site"]
	env["FRAPPE_BENCH"] = paths["bench_path"]

	from mcp_ui.ai.providers import get_provider_config

	provider_config = get_provider_config()
	provider = provider_config.get("provider") or settings.ai_provider or "OpenAI"
	api_key = provider_config.get("api_key", "")

	if provider == "Ollama":
		env["OLLAMA_API_KEY"] = api_key or "ollama-local"
	elif provider == "OpenAI" and api_key:
		env["OPENAI_API_KEY"] = api_key
	elif provider == "Anthropic" and api_key:
		env["ANTHROPIC_API_KEY"] = api_key
	elif provider == "Google" and api_key:
		env["GEMINI_API_KEY"] = api_key

	return env


def start_gateway():
	paths = _get_paths()
	settings = frappe.get_single("MCP Settings")

	if not _is_openclaw_installed(paths):
		frappe.logger("openclaw").warning("OpenClaw not installed. Run install_openclaw() first.")
		return None

	if _is_running(paths["pid_file"]):
		return _read_pid(paths["pid_file"])

	if not _has_config(paths):
		try:
			from mcp_ui.api.openclaw import generate_config

			generate_config()
		except Exception as exc:
			frappe.logger("openclaw").error(f"Failed to generate config: {exc}")
			write_runtime_state(error=str(exc), last_start_attempt=_utcnow())
			try:
				settings.db_set("openclaw_last_gateway_error", str(exc), update_modified=False)
			except Exception:
				pass
			return None

	refresh_site_context(reason="gateway_start")
	node_bin = _discover_node_binary()
	if not node_bin:
		write_runtime_state(error="Node 22+ not available", last_start_attempt=_utcnow())
		try:
			settings.db_set("openclaw_last_gateway_error", "Node 22+ not available", update_modified=False)
		except Exception:
			pass
		return None

	sanitize_stats = _sanitize_session_store(paths)
	env = _build_gateway_env(settings, paths)
	os.makedirs(os.path.dirname(paths["log_file"]), exist_ok=True)
	log_fd = open(paths["log_file"], "a")

	try:
		process = subprocess.Popen(
			[node_bin, paths["openclaw_entry"], "gateway"],
			cwd=paths["workspace"],
			stdout=log_fd,
			stderr=log_fd,
			env=env,
			start_new_session=True,
		)
	except Exception as exc:
		log_fd.close()
		frappe.logger("openclaw").error(f"Failed to start gateway: {exc}")
		write_runtime_state(error=str(exc), last_start_attempt=_utcnow(), node=node_bin)
		try:
			settings.db_set("openclaw_last_gateway_error", str(exc), update_modified=False)
		except Exception:
			pass
		return None

	with open(paths["pid_file"], "w") as handle:
		handle.write(str(process.pid))

	state = write_runtime_state(
		last_started_at=_utcnow(),
		last_start_attempt=_utcnow(),
		last_pid=process.pid,
		node=node_bin,
		error="",
	)
	write_json(paths["heartbeat_file"], {"pid": process.pid, "started_at": state["last_started_at"]})
	try:
		settings.db_set("openclaw_last_gateway_start", state["last_started_at"], update_modified=False)
		settings.db_set("openclaw_last_gateway_error", "", update_modified=False)
	except Exception:
		pass

	if sanitize_stats["snapshots_cleared"] or sanitize_stats["locks_removed"]:
		frappe.logger("openclaw").info(
			"OpenClaw session store sanitized before startup "
			f"(snapshots_cleared={sanitize_stats['snapshots_cleared']}, locks_removed={sanitize_stats['locks_removed']})"
		)
	frappe.logger("openclaw").info(f"OpenClaw gateway started (PID {process.pid})")
	return process.pid


def stop_gateway():
	paths = _get_paths()
	pid = _read_pid(paths["pid_file"])
	if not pid:
		return False

	try:
		os.kill(pid, signal.SIGTERM)
	except (ProcessLookupError, PermissionError, OSError):
		pass

	try:
		os.unlink(paths["pid_file"])
	except OSError:
		pass

	write_runtime_state(last_stopped_at=_utcnow())
	return True


def ensure_gateway_running():
	if not _is_openclaw_enabled():
		return

	paths = _get_paths()
	if _is_running(paths["pid_file"]):
		write_runtime_state(last_seen_alive_at=_utcnow())
		return

	if not _is_openclaw_installed(paths):
		result = install_openclaw()
		if not result.get("success"):
			frappe.logger("openclaw").error(f"Auto-install failed: {result.get('error')}")
			write_runtime_state(error=result.get("error"), last_start_attempt=_utcnow())
			return

	pid = start_gateway()
	if pid:
		frappe.logger("openclaw").info(f"OpenClaw gateway auto-started by scheduler (PID {pid})")


def get_status():
	paths = _get_paths()
	running = _is_running(paths["pid_file"])
	state = read_json(paths["state_file"], {}) or {}

	return {
		"enabled": _is_openclaw_enabled(),
		"installed": _is_openclaw_installed(paths),
		"configured": _has_config(paths),
		"running": running,
		"pid": _read_pid(paths["pid_file"]) if running else None,
		"runtime_root": paths["root"],
		"config_file": paths["config_file"],
		"workspace": paths["workspace"],
		"log_file": paths["log_file"],
		"state": state,
	}
