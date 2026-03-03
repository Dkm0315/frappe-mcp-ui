# Frappe AI IDE — Design Document

## Vision

A web-based AI-powered IDE for Frappe that serves three audiences from one product:

1. **Admins** (Control Panel) — manage tools, channels, feature flags, access control
2. **Developers** (IDE) — script editor, workflow builder, schema manager, API explorer
3. **Business Users** (Assistant) — chat interface, quick actions, web preview of messaging channels

## Architecture

### Three Modes

Mode selector in TopBar. Sidebar navigation changes per mode.

**Control Panel (Admin):**
- Dashboard — Bento Cards metrics, Animated Collection for recent AI activity, channel health
- Tools — MCP tool execution with Multi-Step Form wizard, Animated Collection with view switching
- Feature Flags — per-DocType/per-tool/per-channel toggles, autonomy matrix
- Channels — Telegram/WhatsApp/WebChat config via OpenClaw
- Access Control — per-DocType CRUD permissions, field whitelists
- History — execution log with Stacked List
- Settings — Vertical Tabs for preferences

**IDE (Developer):**
- Script Studio — Monaco editor for Client Scripts + Server Scripts + Notifications, AI assistant sidebar
- Workflow Builder — visual state machine editor, AI-generated workflows
- Schema Manager — Fluid Expanding Grid for DocTypes, Custom Fields, Property Setters
- API Explorer — test any Frappe API, see request/response
- Debug Console — script execution logs, error traces

**Assistant (End-User):**
- Chat — web-based AI chat (same engine as Telegram/WhatsApp)
- Quick Actions — configurable per-role action buttons
- My Activity — personal history
- Favorites — bookmarked tools/workflows

### Feature Flag System

Stored in MCP Settings (SingleDocType) with child tables:

**Global Flags:**
- enable_script_studio, enable_workflow_builder, enable_schema_manager
- enable_channels, enable_ai_autonomy, enable_developer_mode

**Per-DocType Config (child table: MCP DocType Config):**
- doctype, allow_ai_read, allow_ai_create, allow_ai_update, allow_ai_delete
- allow_client_scripts, allow_server_scripts, allow_workflow, allow_custom_fields
- require_confirmation, use_browser_simulation, field_whitelist

**Per-Tool Config (child table: MCP Tool Config):**
- tool_name, enabled, allowed_roles, max_daily_executions

**Per-Channel Config:**
- telegram_enabled, whatsapp_enabled, webchat_enabled

### Hybrid Execution Model

- **Reads** (get_list, search, reports): API-first (fast, 100ms)
- **Writes** (create, update, delete, submit): Configurable per DocType
  - Simple DocTypes: API (triggers server hooks, skips client scripts)
  - Complex DocTypes (flagged `use_browser_simulation`): Playwright headless browser

### Graceful Degradation

Three capability states detected on startup:
1. **Full** — server_script_enabled=1, Script Manager role present
2. **Partial** — server scripts disabled → Client Scripts, Workflows, Custom Fields work; Server Scripts tab greyed out with explanation
3. **Read-only** — missing Script Manager role → can view but not create scripts

### Notification Management

Script Studio includes Notifications tab for managing:
- Notification DocType rules (email + system, triggered by doc events)
- Notification Log viewing (bell icon history)
- Email Queue monitoring

### Private App Discovery

No GitHub access needed. All customizations discovered via database:
- DocType schema via frappe.get_meta()
- Client/Server Scripts via API
- Custom Fields, Property Setters, Workflows via API
- Hooks discovery via frappe.get_hooks()

## uselayouts Components

| Component | Where Used |
|-----------|-----------|
| Animated Collection | Tools grid, Dashboard activity, Chat results |
| Bento Card | Dashboard metrics |
| Multi-Step Form | Tool execution wizard, Create Document flow |
| Vertical Tabs | Settings, Script Studio sidebar |
| Filter Interaction | Tools category filter, Schema Manager |
| Status Button | Channel health, Workflow states |
| Stacked List | History, Workflow list |
| Fluid Expanding Grid | Schema Manager DocType browser |
| Inline Edit | Script enable/disable, Feature flag toggles |
| Delete Button | Destructive operations with confirmation |
| Morphing Input | Chat input, AI prompt |
| Discrete Tabs | Feature Flags categories |
| Dynamic Toolbar | Contextual actions |

## AI Automation Capabilities

All via Frappe REST API (no file access needed):
- Create Custom DocTypes
- Add Custom Fields to any DocType
- Write Client Scripts (JavaScript, Form/List views)
- Write Server Scripts (Python, sandboxed — DocType Events, Schedulers, APIs, Permission Queries)
- Create Workflows (States, Transitions, Conditions, Roles)
- Modify field properties via Property Setter
- Create Notification rules
- Generate reports
- Chain multi-step automations

## Implementation Priority (This Session)

1. Fix SmartForm (replace cmdk with custom autocomplete)
2. Install uselayouts components
3. Build mode switcher + sidebar per mode
4. Rewrite Dashboard with Bento Cards + Animated Collection
5. Rewrite Tools with Animated Collection + Multi-Step Form
6. Build Script Studio (basic: list/create/edit scripts)
7. Build Feature Flags page
8. Build Workflow Builder (basic: list + visual editor)
9. Build Schema Manager
10. Build Chat/Assistant page
