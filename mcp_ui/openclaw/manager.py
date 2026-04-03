"""
OpenClaw Gateway Process Manager

Keeps the OpenClaw gateway running via Frappe scheduler.
Works on Frappe Cloud, self-hosted, and local dev environments.

The scheduler calls `ensure_gateway_running` every minute.
If the gateway is not running and OpenClaw is enabled in MCP Settings,
it starts the process automatically.
"""
import hashlib
import json
import os
import signal
import subprocess
import sys

import frappe


OPENCLAW_NODE_VERSION = os.environ.get("MCP_UI_OPENCLAW_NODE_VERSION", "24")


def _get_paths():
	"""Get all relevant paths for OpenClaw."""
	bench_path = frappe.utils.get_bench_path()
	app_path = os.path.join(bench_path, "apps", "mcp_ui")
	openclaw_runtime = os.path.join(app_path, "openclaw_runtime")
	openclaw_bin = _resolve_openclaw_executable(openclaw_runtime)
	python_bin = os.path.join(openclaw_runtime, ".venv", "bin", "python")
	pid_file = os.path.join(bench_path, "config", "openclaw.pid")
	log_file = os.path.join(bench_path, "logs", "openclaw.log")
	config_dir = os.path.expanduser("~/.openclaw")
	config_file = os.path.join(config_dir, "openclaw.json")

	return {
		"bench_path": bench_path,
		"app_path": app_path,
		"openclaw_runtime": openclaw_runtime,
		"openclaw_bin": openclaw_bin,
		"python_bin": python_bin,
		"pid_file": pid_file,
		"log_file": log_file,
		"config_dir": config_dir,
		"config_file": config_file,
	}


def _is_running(pid_file: str) -> bool:
	"""Check if the gateway process is still alive."""
	if not os.path.exists(pid_file):
		return False

	try:
		with open(pid_file) as f:
			pid = int(f.read().strip())
		# Signal 0 checks if process exists without killing it
		os.kill(pid, 0)
		return True
	except (ValueError, ProcessLookupError, PermissionError, OSError):
		# PID file exists but process is dead — clean up
		try:
			os.unlink(pid_file)
		except OSError:
			pass
		return False


def _is_openclaw_enabled() -> bool:
	"""Check if OpenClaw is enabled in MCP Settings."""
	try:
		return bool(frappe.db.get_single_value("MCP Settings", "openclaw_enabled"))
	except Exception:
		return False


def _is_openclaw_installed(paths: dict) -> bool:
	"""Check if openclaw binary exists."""
	return os.path.isfile(paths["openclaw_bin"])


def _has_config(paths: dict) -> bool:
	"""Check if openclaw.json exists."""
	return os.path.isfile(paths["config_file"])


def install_openclaw():
	"""Install openclaw and openclaw-mcp-adapter npm packages.

	Called during after_install and can be called manually via bench command.
	"""
	paths = _get_paths()
	runtime_dir = paths["openclaw_runtime"]
	os.makedirs(runtime_dir, exist_ok=True)

	# Create package.json if it doesn't exist
	pkg_json = os.path.join(runtime_dir, "package.json")
	if not os.path.exists(pkg_json):
		import json
		with open(pkg_json, "w") as f:
			json.dump({
				"name": "mcp-ui-openclaw-runtime",
				"private": True,
				"dependencies": {
					"openclaw": "latest",
					"openclaw-mcp-adapter": "latest",
				},
			}, f, indent=2)

	python_result = _ensure_python_runtime(paths)
	if not python_result.get("success"):
		return python_result

	# Run npm install under Node 24 via nvm when available
	try:
		result = _run_node_command(
			command="npm install --production",
			cwd=runtime_dir,
			timeout=300,
		)
		if result.returncode == 0:
			frappe.logger("openclaw").info("OpenClaw npm packages installed successfully")
			return {
				"success": True,
				"output": result.stdout,
				"python_runtime": python_result,
				"node_version": OPENCLAW_NODE_VERSION,
			}
		else:
			frappe.logger("openclaw").error(f"npm install failed: {result.stderr}")
			return {"success": False, "error": result.stderr}
	except FileNotFoundError:
		return {"success": False, "error": "npm not found. Install Node.js first."}
	except subprocess.TimeoutExpired:
		return {"success": False, "error": "npm install timed out after 120s"}


def start_gateway():
	"""Start the OpenClaw gateway as a background process.

	Returns the PID of the started process, or None if it failed.
	"""
	paths = _get_paths()

	if not _is_openclaw_installed(paths):
		frappe.logger("openclaw").warning("OpenClaw not installed. Run install_openclaw() first.")
		return None

	sync_result = sync_gateway_config(paths=paths)
	if sync_result.get("changed") and _is_running(paths["pid_file"]):
		stop_gateway()

	if _is_running(paths["pid_file"]):
		with open(paths["pid_file"]) as f:
			return int(f.read().strip())

	if not sync_result.get("success") and not _has_config(paths):
		# Auto-generate config
		try:
			from mcp_ui.api.openclaw import generate_config
			generate_config()
		except Exception as e:
			frappe.logger("openclaw").error(f"Failed to generate config: {e}")
			return None
		sync_gateway_config(paths=paths)

	# Build environment — pass through LLM API keys
	env = os.environ.copy()
	settings = frappe.get_single("MCP Settings")
	provider = settings.ai_provider or "OpenAI"

	# Set the API key env var for the LLM provider
	from mcp_ui.ai.providers import get_provider_config
	provider_config = get_provider_config()
	api_key = provider_config.get("api_key", "")

	if provider == "Ollama":
		env["OLLAMA_API_KEY"] = api_key or "ollama-local"
	elif provider == "OpenAI" and api_key:
		env["OPENAI_API_KEY"] = api_key
	elif provider == "Anthropic" and api_key:
		env["ANTHROPIC_API_KEY"] = api_key
	elif provider == "Google" and api_key:
		env["GEMINI_API_KEY"] = api_key

	# Ensure logs directory exists
	os.makedirs(os.path.dirname(paths["log_file"]), exist_ok=True)

	# Start gateway as detached subprocess
	log_fd = open(paths["log_file"], "a")
	try:
		process = _popen_node_command(
			command=f'"{paths["openclaw_bin"]}" gateway',
			cwd=os.path.expanduser("~"),
			env=env,
			stdout=log_fd,
			stderr=log_fd,
		)
	except Exception as e:
		log_fd.close()
		frappe.logger("openclaw").error(f"Failed to start gateway: {e}")
		return None

	# Write PID file
	os.makedirs(os.path.dirname(paths["pid_file"]), exist_ok=True)
	with open(paths["pid_file"], "w") as f:
		f.write(str(process.pid))

	try:
		settings = frappe.get_single("MCP Settings")
		settings.openclaw_status = f"Running (PID {process.pid})"
		settings.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		pass

	frappe.logger("openclaw").info(f"OpenClaw gateway started (PID {process.pid})")
	return process.pid


def stop_gateway():
	"""Stop the OpenClaw gateway process."""
	paths = _get_paths()
	pid_file = paths["pid_file"]

	if not os.path.exists(pid_file):
		return False

	try:
		with open(pid_file) as f:
			pid = int(f.read().strip())

		# Send SIGTERM for graceful shutdown
		os.kill(pid, signal.SIGTERM)
		frappe.logger("openclaw").info(f"OpenClaw gateway stopped (PID {pid})")
	except (ValueError, ProcessLookupError, PermissionError):
		pass

	try:
		os.unlink(pid_file)
	except OSError:
		pass

	try:
		settings = frappe.get_single("MCP Settings")
		settings.openclaw_status = "Stopped"
		settings.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		pass

	return True


def ensure_gateway_running():
	"""Scheduler job: ensure the OpenClaw gateway is running.

	Called every minute by the Frappe scheduler. If OpenClaw is enabled
	in MCP Settings but the process is not running, it starts it.
	"""
	if not _is_openclaw_enabled():
		return

	paths = _get_paths()
	sync_result = sync_gateway_config(paths=paths)

	if _is_running(paths["pid_file"]):
		if sync_result.get("changed"):
			frappe.logger("openclaw").info("OpenClaw config changed in MCP Settings, restarting gateway.")
			stop_gateway()
			pid = start_gateway()
			if pid:
				frappe.logger("openclaw").info(f"OpenClaw gateway restarted by scheduler (PID {pid})")
		return  # Already running, nothing to do

	if not _is_openclaw_installed(paths):
		# Try to install on first run
		frappe.logger("openclaw").info("OpenClaw not installed, attempting install...")
		result = install_openclaw()
		if not result.get("success"):
			frappe.logger("openclaw").error(f"Auto-install failed: {result.get('error')}")
			return

	# Start the gateway
	pid = start_gateway()
	if pid:
		frappe.logger("openclaw").info(f"OpenClaw gateway auto-started by scheduler (PID {pid})")


def get_status():
	"""Get current gateway status."""
	paths = _get_paths()
	running = _is_running(paths["pid_file"])
	installed = _is_openclaw_installed(paths)
	enabled = _is_openclaw_enabled()
	has_cfg = _has_config(paths)

	pid = None
	if running:
		try:
			with open(paths["pid_file"]) as f:
				pid = int(f.read().strip())
		except Exception:
			pass

	return {
		"enabled": enabled,
		"installed": installed,
		"has_config": has_cfg,
		"running": running,
		"pid": pid,
		"node_version": OPENCLAW_NODE_VERSION,
		"runtime_python": paths["python_bin"],
		"openclaw_bin": paths["openclaw_bin"],
		"config_file": paths["config_file"],
		"config_checksum": frappe.db.get_single_value("MCP Settings", "openclaw_config_checksum"),
		"log_file": paths["log_file"],
	}


def sync_gateway_config(paths: dict | None = None) -> dict:
	"""Write ~/.openclaw/openclaw.json from the JSON stored in MCP Settings."""
	paths = paths or _get_paths()
	try:
		settings = frappe.get_single("MCP Settings")
	except Exception as exc:
		return {"success": False, "changed": False, "error": str(exc)}

	raw_config = (settings.get("openclaw_config_json") or "").strip()
	if not raw_config:
		if not settings.get("openclaw_config_path"):
			settings.openclaw_config_path = paths["config_file"]
			settings.save(ignore_permissions=True)
			frappe.db.commit()
		return {"success": False, "changed": False, "error": "No OpenClaw config JSON stored in MCP Settings."}

	try:
		config_payload = frappe.parse_json(raw_config)
	except Exception as exc:
		frappe.logger("openclaw").error(f"Stored OpenClaw config JSON is invalid: {exc}")
		return {"success": False, "changed": False, "error": "Stored OpenClaw config JSON is invalid."}

	normalized = json.dumps(config_payload, indent=2, sort_keys=True)
	checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
	existing_payload = ""
	if os.path.exists(paths["config_file"]):
		try:
			with open(paths["config_file"], encoding="utf-8") as f:
				existing_payload = f.read()
		except OSError:
			existing_payload = ""

	changed = existing_payload.strip() != normalized.strip()
	if changed:
		os.makedirs(paths["config_dir"], exist_ok=True)
		with open(paths["config_file"], "w", encoding="utf-8") as f:
			f.write(f"{normalized}\n")

	if (
		settings.get("openclaw_config_path") != paths["config_file"]
		or settings.get("openclaw_config_checksum") != checksum
		or changed
	):
		settings.openclaw_config_path = paths["config_file"]
		settings.openclaw_config_checksum = checksum
		settings.openclaw_config_synced_at = str(frappe.utils.now_datetime())
		settings.openclaw_status = "Config Synced" if not _is_running(paths["pid_file"]) else "Running"
		settings.save(ignore_permissions=True)
		frappe.db.commit()

	return {
		"success": True,
		"changed": changed,
		"checksum": checksum,
		"config_file": paths["config_file"],
	}


def _ensure_python_runtime(paths: dict) -> dict:
	"""Create a runtime venv with MCP deps while keeping the bench env unchanged."""
	runtime_python = paths["python_bin"]
	runtime_dir = paths["openclaw_runtime"]
	venv_dir = os.path.dirname(os.path.dirname(runtime_python))
	if not os.path.exists(runtime_python):
		create_result = subprocess.run(
			[
				sys.executable,
				"-m",
				"venv",
				"--system-site-packages",
				venv_dir,
			],
			cwd=runtime_dir,
			capture_output=True,
			text=True,
			timeout=120,
		)
		if create_result.returncode != 0:
			return {"success": False, "error": create_result.stderr or create_result.stdout}

	install_result = subprocess.run(
		[
			runtime_python,
			"-m",
			"pip",
			"install",
			"mcp>=1.0.0",
		],
		cwd=runtime_dir,
		capture_output=True,
		text=True,
		timeout=300,
	)
	if install_result.returncode != 0:
		return {"success": False, "error": install_result.stderr or install_result.stdout}
	return {
		"success": True,
		"python": runtime_python,
		"output": install_result.stdout,
	}


def _run_node_command(command: str, cwd: str, timeout: int) -> subprocess.CompletedProcess:
	return subprocess.run(
		_build_node_shell_command(command),
		cwd=cwd,
		capture_output=True,
		text=True,
		timeout=timeout,
	)


def _popen_node_command(
	command: str,
	cwd: str,
	env: dict[str, str],
	stdout,
	stderr,
) -> subprocess.Popen:
	return subprocess.Popen(
		_build_node_shell_command(command),
		cwd=cwd,
		stdout=stdout,
		stderr=stderr,
		env=env,
		start_new_session=True,
	)


def _build_node_shell_command(command: str) -> list[str]:
	nvm_script = os.path.expanduser("~/.nvm/nvm.sh")
	if os.path.exists(nvm_script):
		return [
			"bash",
			"-lc",
			f'source "{nvm_script}" && nvm use {OPENCLAW_NODE_VERSION} >/dev/null && exec {command}',
		]
	return ["bash", "-lc", f"exec {command}"]


def _resolve_openclaw_executable(openclaw_runtime: str) -> str:
	bin_path = os.path.join(openclaw_runtime, "node_modules", ".bin", "openclaw")
	if os.path.isfile(bin_path):
		return bin_path
	package_script = os.path.join(
		openclaw_runtime,
		"node_modules",
		"openclaw",
		"openclaw.mjs",
	)
	if os.path.isfile(package_script):
		return package_script
	return bin_path
