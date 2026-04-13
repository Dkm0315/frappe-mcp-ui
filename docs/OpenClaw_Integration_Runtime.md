# OpenClaw Integration Runtime Guide

This document describes the current `mcp_ui` OpenClaw integration as implemented in this repo. It is intended as an implementation handoff for future code changes, including use with Claude Code or other coding agents.

This is not a product PRD. It documents:

- the runtime architecture
- how user federation works
- where config and state live
- how Telegram/OpenClaw/Frappe interact
- what has been customized already
- how to extend or debug the integration safely


## 1. Scope

The current integration is a **bench-colocated OpenClaw gateway** for Frappe.

It supports:

- a bench-local OpenClaw runtime
- Telegram channel integration
- Frappe-side user federation
- request-scoped impersonation of mapped ERP users
- planner-driven tool orchestration
- generated site context, skills, and `SOUL.md`
- scheduler/watchdog style gateway management
- browser/Playwright settings in `MCP Settings`

The primary app is `apps/mcp_ui`.


## 2. High-Level Architecture

The data flow is:

1. A provider message reaches OpenClaw, usually Telegram.
2. OpenClaw loads the native plugin `frappe-federated`.
3. The plugin forwards session metadata to a Python bridge.
4. The Python bridge boots Frappe for the current site.
5. Frappe resolves the external sender to a mapped ERP user.
6. Planner/retrieval/execution runs as that mapped user.
7. The result is returned back through OpenClaw to the provider.

The system is intentionally split into:

- OpenClaw runtime and plugin layer
- Frappe bridge layer
- Frappe federation/planner/execution layer
- generated context and skill layer


## 3. Main Files

### Frappe API and config generation

- `apps/mcp_ui/mcp_ui/api/openclaw.py`

Responsibilities:

- generate bench-local OpenClaw config
- generate `SOUL.md`
- status endpoints
- gateway start/restart helpers
- provisioning helpers for Telegram users and mappings

### Runtime paths and state

- `apps/mcp_ui/mcp_ui/openclaw/runtime.py`

Responsibilities:

- define bench-local runtime paths
- read/write JSON state
- manage session state store

### Gateway lifecycle

- `apps/mcp_ui/mcp_ui/openclaw/manager.py`

Responsibilities:

- discover Node 22+/24
- start the OpenClaw gateway
- stop/restart gateway
- sanitize session stores
- write runtime state

### User federation and execution

- `apps/mcp_ui/mcp_ui/openclaw/federation.py`

Responsibilities:

- resolve external senders to Frappe users
- maintain session mode
- impersonate mapped users
- enforce confirmation/admin mode for writes
- audit action execution

### Planner and retrieval

- `apps/mcp_ui/mcp_ui/openclaw/planner.py`
- `apps/mcp_ui/mcp_ui/openclaw/site_context.py`
- `apps/mcp_ui/mcp_ui/openclaw/actions.py`

Responsibilities:

- classify vague requests
- retrieve candidate doctypes/reports/workflows/actions
- produce plan steps and answer constraints
- surface action metadata

### Bridge process

- `apps/mcp_ui/mcp_ui/openclaw/plugin_bridge.py`

Responsibilities:

- initialize Frappe from a subprocess
- dispatch OpenClaw plugin operations into Python/Frappe

### Native OpenClaw plugin

- `apps/mcp_ui/openclaw_runtime/plugins/frappe-federated/index.js`
- `apps/mcp_ui/openclaw_runtime/plugins/frappe-federated/openclaw.plugin.json`

Responsibilities:

- expose OpenClaw tools
- build provider session context
- call the Python bridge
- compact planner output before it reaches the model

### Settings schema

- `apps/mcp_ui/mcp_ui/mcp_ui/doctype/mcp_settings/mcp_settings.json`
- `apps/mcp_ui/mcp_ui/mcp_ui/doctype/openclaw_identity_mapping/openclaw_identity_mapping.json`
- `apps/mcp_ui/mcp_ui/public/js/mcp_settings.js`

Responsibilities:

- store runtime/provider/browser/Telegram settings
- store external identity mappings
- expose Desk buttons to generate config and restart gateway


## 4. Bench-Local Runtime Layout

The runtime is site-scoped and lives under:

```text
sites/<site>/private/openclaw/
```

Important paths are defined in `runtime.py`.

For `site1.local`, current layout is:

```text
sites/site1.local/private/openclaw/
├── home/
│   └── .openclaw/
│       └── openclaw.json
├── manifest/
│   ├── current.json
│   ├── previous.json
│   └── last_diff.json
├── workspace/
│   ├── SOUL.md
│   └── skills/
├── runtime_state.json
├── session_state.json
├── openclaw.pid
└── heartbeat.json
```

Logs live under:

```text
logs/openclaw/<site>.log
```

This design avoids using global `~/.openclaw` as the primary runtime root.


## 5. User Federation

### Current federation model

Federation is enforced in **Frappe**, not Telegram.

OpenClaw admits the Telegram DM at the gateway layer, then Frappe decides whether that sender is mapped to a real ERP user.

### Current matching order

In `federation.py`, sender resolution checks:

1. `external_username`
2. `external_id` as a legacy fallback

Additional optional restrictions can be applied:

- `site`
- `allowed_chat_id`
- `allowed_thread_id`

### Important implementation detail

The primary production path is now:

- Telegram username -> mapped Frappe user email

The `external_id` field still exists in the data model as a fallback, but it is hidden in the UI and is no longer required for normal setup.

### Relevant files

- `apps/mcp_ui/mcp_ui/openclaw/federation.py`
- `apps/mcp_ui/mcp_ui/mcp_ui/doctype/openclaw_identity_mapping/openclaw_identity_mapping.json`
- `apps/mcp_ui/mcp_ui/public/js/mcp_settings.js`

### Example mapping

```text
channel = telegram
external_username = dkm0315
frappe_user = dhairya15marwaha@gmail.com
site = site1.local
enabled = 1
```

### What happens after match

Once a mapping is found:

- the mapped user is loaded
- roles are returned
- all reads/writes execute inside `impersonate_user(...)`

There is no permanent business execution as `Administrator`.

`Administrator` is only the boot user for the bridge process itself.


## 6. Telegram Runtime Model

### Current OpenClaw config behavior

`generate_config()` now writes Telegram config like this:

- `dmPolicy: "open"`
- `allowFrom: ["*"]`

This is intentional.

OpenClaw no longer enforces Telegram-user allowlisting as the main security layer. Instead:

- OpenClaw accepts the DM
- the plugin forwards Telegram sender metadata
- Frappe federation decides whether the sender is mapped and allowed

This makes production setup workable without manually collecting Telegram numeric IDs.

### Username handling

The native plugin extracts the username from the provider context and normalizes it by stripping `@`.

That logic lives in:

- `apps/mcp_ui/openclaw_runtime/plugins/frappe-federated/index.js`


## 7. Planner and Orchestration

### Why the planner exists

The model should not directly freestyle against the entire action/tool surface.

The planner layer exists to:

- classify intent
- retrieve likely doctypes/reports/workflows/actions
- determine missing inputs
- determine write confirmation requirements
- determine mode requirements

### Main planner outputs

Planner output can include:

- `intents`
- `top_doctype`
- `top_report`
- `related_reports`
- `answer_constraints`
- `permission_summary`
- `candidate_actions`
- `plan_steps`
- `confirmation_required`
- `create_plan`

### Important runtime change

The OpenClaw plugin now compacts planner output before passing it to the model. This prevents the model from overfitting on irrelevant cross-module retrieval results.

The plugin returns a scoped payload with:

- `scope`
- `resolution`
- `permission_summary`
- `plan_steps`
- `candidate_actions`

instead of the full raw retrieval tree.

### Design rule

The planner must stay generic.

Do not add prompt logic that assumes:

- Helpdesk exists
- CRM exists
- a site has a specific app/module
- a question about “tickets” must always mean Helpdesk

If a site has custom modules, the planner should arrive there through retrieval and permissions, not hardcoded prompt shaping.


## 8. Action Execution Model

All business execution goes through `execute_as_mapped_user(...)` in `federation.py`.

### Important design rule

CRUD is an execution substrate, not the product surface.

That means:

- `get_list`, `get_document`, `create_document`, `update_document`, `delete_document`
- bulk operations
- submit/cancel/amend primitives

should be treated as low-level actions.

The user-facing behavior should be driven by:

- planner output
- module-aware retrieval
- workflow capabilities
- report capabilities
- generated skills
- plugin-level orchestration

This matters because the end user is not asking for CRUD. The end user is asking for:

- a report
- a layered workflow
- a short path through a complex process
- a business outcome without needing to understand the UI

The runtime should therefore plan in business terms first and drop to CRUD primitives only at the execution layer.

### Execution guarantees

- user is resolved first
- request runs as the mapped ERP user
- confirmation is required for writes
- admin mode is required for customization/admin actions
- permission errors are surfaced as structured statuses

### Structured statuses

Execution returns statuses such as:

- `success`
- `needs_clarification`
- `permission_denied`
- `validation_failed`
- `confirmation_required`
- `transient_failure`

### Admin mode

Session mode is stored in the bench-local session state file.

Modes:

- `normal`
- `admin`

Admin-only work includes:

- custom fields
- property setters
- workflow design changes
- client/server script changes
- funnel design/update


## 9. Site Context, Manifest, and Skills

The site context layer builds a generated knowledge pack from the live site and codebase.

### Main outputs

- site manifest
- manifest diff
- generated skills
- `SOUL.md`

### Content sources

The manifest can include:

- installed apps
- modules
- doctypes
- reports
- workflows
- pages/workspaces
- custom fields
- property setters
- hooks
- permission logic
- NextAI context

### Generated skills

Skills are generated under:

```text
sites/<site>/private/openclaw/workspace/skills
```

These are per-site generated artifacts, not static repo docs.

### `SOUL.md`

`SOUL.md` is the site-level startup instruction set for OpenClaw.

Important rule: it should stay generic and planner-driven. Avoid domain-specific hacks there.


## 10. Browser / Playwright Support

The Frappe settings model includes browser runtime fields that are pushed into generated OpenClaw config.

Current relevant settings include:

- browser enabled
- headless
- default profile
- executable path

These become part of the generated `openclaw.json`.

This allows:

- browser automation from OpenClaw
- Playwright-backed UI actions where needed

The Desk UI for `MCP Settings` was verified through Playwright during implementation.


## 11. Settings UI

The `MCP Settings` form currently exposes buttons for:

- `Generate OpenClaw Config`
- `Restart Gateway`
- `Setup Telegram User`

The setup dialog now asks for:

- Frappe user email
- full name
- Telegram username
- send welcome email

It does **not** require the Telegram numeric ID anymore.


## 12. Provider Model Selection

Provider selection is managed in `MCP Settings`.

### Current behavior

- if configured provider credentials exist, use them
- if no API key is available for the configured hosted provider, fall back to Ollama

The current generated runtime can use:

- OpenAI
- Anthropic
- Google
- Ollama

Current local fallback model in this bench has been:

```text
ollama/qwen3:8b
```

### Important operational note

The bot may still perform better on stronger hosted models.

Prompt fixes and planner changes are necessary, but they do not remove the need for a capable model on difficult multi-step business tasks.


## 13. Gateway Lifecycle

### Install

OpenClaw runtime dependencies are installed in:

```text
apps/mcp_ui/openclaw_runtime/
```

### Start

Preferred:

```bash
bench --site <site> execute mcp_ui.api.openclaw.start_gateway
```

### Restart

```bash
bench --site <site> execute mcp_ui.api.openclaw.restart_gateway
```

### Regenerate config

```bash
bench --site <site> execute mcp_ui.api.openclaw.generate_config
```

### Status

```bash
bench --site <site> execute mcp_ui.api.openclaw.get_openclaw_status
```

### What the manager handles

The manager:

- discovers Node 22+
- checks config presence
- refreshes site context before boot
- starts the gateway with a bench-local `HOME`
- writes PID/runtime state
- sanitizes stale session-store artifacts


## 14. Known Good Current State

At the time of writing, the implementation has already been validated for:

- bench-local config generation
- gateway restart
- Telegram username-based federation
- planner execution through the native plugin
- settings form controls in Desk
- browser settings propagation into `openclaw.json`

Also confirmed:

- mapped users only see what Frappe permissions allow
- report access is properly denied when the mapped user cannot run the report


## 15. Known Limitations

### 1. Retrieval quality still needs more work

The planner is now less prompt-hacked, but retrieval quality is still partly token/synonym driven.

Next improvement should be:

- manifest-derived dynamic expansion
- better typed ranking
- less dependence on static token synonyms

### 2. Model quality still matters

Weak local models can still underperform on:

- long analytical questions
- multi-step workflow reasoning
- ambiguous business asks

### 3. Some admin actions still need payload normalization

The gating is in place, but a few admin/customization actions may still need better argument assembly for fully natural chat-driven execution.

### 4. Federation is username-centric

This is better operationally than numeric ID capture, but it assumes Telegram usernames are stable enough for the deployment model.

If a stricter trust boundary is needed later, `external_id` can still be reintroduced as a second factor or silent backend-only fallback.


## 16. Extension Guidelines

### If you are changing federation

Start here:

- `mcp_ui/openclaw/federation.py`
- `mcp_ui/api/openclaw.py`
- `openclaw_runtime/plugins/frappe-federated/index.js`

Rules:

- keep Frappe as the source of truth for authorization
- do not trust provider metadata alone
- avoid returning to permanent numeric Telegram allowlists unless there is a strong operational reason

### If you are changing planner behavior

Start here:

- `mcp_ui/openclaw/planner.py`
- `mcp_ui/openclaw/site_context.py`
- `openclaw_runtime/plugins/frappe-federated/index.js`

Rules:

- prefer generic planner constraints over domain-specific prompt hacks
- avoid app/module assumptions unless retrieval proves them
- keep model-facing planner payload small and scoped

### If you are changing tool execution

Start here:

- `mcp_ui/openclaw/federation.py`
- `mcp_ui/openclaw/actions.py`
- `mcp_ui/ai/tools.py`

Rules:

- preserve request-scoped impersonation
- preserve write confirmation
- preserve admin mode gating

### If you are changing runtime config

Start here:

- `mcp_ui/api/openclaw.py`
- `mcp_ui/openclaw/manager.py`
- `mcp_ui/openclaw/runtime.py`

Rules:

- keep config bench-local
- keep runtime site-scoped
- do not regress to global config/state unless explicitly intended


## 17. Recommended Debug Sequence

When the bot behaves incorrectly, debug in this order:

1. `bench --site <site> execute mcp_ui.api.openclaw.get_openclaw_status`
2. inspect generated `openclaw.json`
3. inspect `logs/openclaw/<site>.log`
4. verify identity resolution:
   `resolve_identity(...)`
5. verify planner result:
   `plan_request(...)`
6. verify actual user-scoped data access:
   `execute_as_user(... get_list ...)`
7. verify actual report access:
   `execute_as_user(... run_report ...)`

This is critical:

- bad answers are not always model errors
- often they are planner scope issues, retrieval issues, or real permission/data issues


## 18. Practical Guidance For Claude Code

When using Claude Code or another agent against this repo:

- treat this doc as the implementation baseline
- prefer changing planner/retrieval/action code over adding prompt hacks
- inspect live Frappe permission behavior before changing answer logic
- keep the plugin payload compact
- keep federation username-first unless there is a concrete security reason to change it
- regenerate config and restart gateway after runtime/plugin changes

After code changes, the minimum operational verification should be:

```bash
bench --site site1.local execute mcp_ui.api.openclaw.generate_config
bench --site site1.local execute mcp_ui.api.openclaw.restart_gateway
bench --site site1.local execute mcp_ui.api.openclaw.get_openclaw_status
```


## 19. Short Summary

The current integration is:

- a bench-colocated OpenClaw runtime
- a Frappe-native federation and execution layer
- a native OpenClaw plugin talking to a Python bridge
- a planner-first orchestration system
- a bench-local generated context and skills system

The key design decisions are:

- federation belongs in Frappe
- execution belongs to the mapped ERP user
- planner output should be compact and scoped
- runtime state should be bench-local and site-local
- domain-specific hardcoding should be minimized
