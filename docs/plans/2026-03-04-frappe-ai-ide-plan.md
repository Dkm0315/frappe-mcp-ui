# Frappe AI IDE — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the MCP UI from a simple tool runner into a three-mode AI-powered IDE for Frappe — Control Panel (admin), IDE (developer), Assistant (end-user).

**Architecture:** Three-mode app with mode-dependent sidebar navigation, feature flags per DocType/tool/channel, and uselayouts animated components throughout. Mode state stored in zustand with persistence. All new IDE features (Script Studio, Workflow Builder, Schema Manager) interact with Frappe via REST API — no file access needed.

**Tech Stack:** React 19.1.1, TypeScript, shadcn/ui, uselayouts (Framer Motion), zustand 5, @tanstack/react-query 5, react-router-dom 7, Tailwind CSS 4, Vite 7

**Build/Test:** `cd /Users/pavankumarmarwaha/Documents/frappe-bench5/apps/mcp_ui/mcp && yarn build` → test at `http://127.0.0.1:8006/mcp`

---

## Phase A: Foundation — Fix Bugs + Upgrade Mode System

### Task 1: Fix SmartForm cmdk Crash (React 19 incompatibility)

The `SmartForm.tsx` autocomplete for Link fields uses cmdk `Command` component which internally uses Radix UI `Presence` — this causes an infinite re-render loop in React 19 (Error #185).

**Files:**
- Modify: `mcp/src/components/tools/SmartForm.tsx`

**Step 1: Replace cmdk autocomplete with custom Popover-based dropdown**

Replace the autocomplete section (lines 200-251 of SmartForm.tsx) with a custom implementation using the same pattern as the working DocTypeSelector in ToolExecutor.tsx. Use a simple Popover + Input + div list instead of Command/CommandInput/CommandItem.

```tsx
// Replace the entire autocomplete block (lines 200-251) with:
{field.input_type === 'autocomplete' && (
  <LinkFieldAutocomplete
    value={value}
    onChange={onChange}
    linkDoctype={field.link_doctype || ''}
    placeholder={`Search ${field.link_doctype}...`}
  />
)}
```

Create `LinkFieldAutocomplete` as a new component in the same file (above FormFieldRenderer):

```tsx
function LinkFieldAutocomplete({
  value,
  onChange,
  linkDoctype,
  placeholder,
}: {
  value: string;
  onChange: (val: string) => void;
  linkDoctype: string;
  placeholder: string;
}) {
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const { data: options } = useQuery({
    queryKey: ['link-options', linkDoctype, search],
    queryFn: async () => {
      if (!linkDoctype) return [];
      const results = await api.searchLinkField(linkDoctype, search || '', 20);
      return results as LinkFieldOption[];
    },
    enabled: isOpen,
  });

  return (
    <div className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            placeholder={placeholder}
          />
        </div>
      </div>
      {value && (
        <div className="mt-1.5 flex items-center gap-2">
          <Badge variant="secondary">{value}</Badge>
          <button
            type="button"
            onClick={() => { onChange(''); setSearch(''); }}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear
          </button>
        </div>
      )}
      {isOpen && options && options.length > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md max-h-60 overflow-y-auto">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-accent text-left"
              onClick={() => {
                onChange(opt.value);
                setSearch('');
                setIsOpen(false);
              }}
            >
              <div className="flex flex-col">
                <span className={value === opt.value ? 'font-medium' : ''}>{opt.label}</span>
                {opt.description && (
                  <span className="text-xs text-muted-foreground">{opt.description}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
}
```

**Step 2: Remove cmdk imports from SmartForm**

Remove line 14: `import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from '@/components/ui/command';`

Remove lines 16-17: `import { Check, ChevronsUpDown } from 'lucide-react';` (Check is no longer used; keep ChevronsUpDown only if used elsewhere — it's not).

Add Badge import if not already present.

**Step 3: Build and verify**

```bash
cd /Users/pavankumarmarwaha/Documents/frappe-bench5/apps/mcp_ui/mcp && yarn build
```

Navigate to Tools → Create Document → select a DocType with Link fields → verify autocomplete works without crash.

**Step 4: Commit**

```bash
git add mcp/src/components/tools/SmartForm.tsx
git commit -m "fix: replace cmdk with custom autocomplete in SmartForm to fix React 19 crash"
```

---

### Task 2: Upgrade UI Store for Three Modes

**Files:**
- Modify: `mcp/src/types/index.ts`
- Modify: `mcp/src/stores/uiStore.ts`

**Step 1: Update UIMode type**

In `types/index.ts`, change line 107:

```typescript
// Old:
export type UIMode = 'simple' | 'advanced' | 'workflows';

// New:
export type UIMode = 'admin' | 'developer' | 'assistant';
```

**Step 2: Add capability detection to UIStore**

In `stores/uiStore.ts`, add new state fields:

```typescript
interface UIState {
  mode: UIMode;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  hasNextAI: boolean;
  // New: capability detection
  serverScriptsEnabled: boolean;
  hasScriptManagerRole: boolean;
  setMode: (mode: UIMode) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setHasNextAI: (has: boolean) => void;
  setServerScriptsEnabled: (enabled: boolean) => void;
  setHasScriptManagerRole: (has: boolean) => void;
}
```

Default `mode` to `'admin'` instead of `'simple'`. Add the two new setters.

**Step 3: Build and verify**

```bash
yarn build
```

Expect: Build succeeds. The mode switcher in TopBar will break (references 'simple'/'advanced') — that's fixed in Task 4.

**Step 4: Commit**

```bash
git add mcp/src/types/index.ts mcp/src/stores/uiStore.ts
git commit -m "feat: upgrade UIMode to admin/developer/assistant with capability detection"
```

---

### Task 3: Update Router with New Pages

**Files:**
- Modify: `mcp/src/router/index.tsx`
- Create: `mcp/src/pages/ScriptStudio.tsx` (placeholder)
- Create: `mcp/src/pages/WorkflowBuilder.tsx` (placeholder)
- Create: `mcp/src/pages/SchemaManager.tsx` (placeholder)
- Create: `mcp/src/pages/FeatureFlags.tsx` (placeholder)
- Create: `mcp/src/pages/Chat.tsx` (placeholder)
- Create: `mcp/src/pages/ApiExplorer.tsx` (placeholder)
- Create: `mcp/src/pages/DebugConsole.tsx` (placeholder)

**Step 1: Create placeholder pages**

Each placeholder page follows this pattern:

```tsx
export function ScriptStudio() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Script Studio</h1>
      <p className="text-muted-foreground">Create and manage Client Scripts and Server Scripts.</p>
    </div>
  );
}
```

Create all 7 placeholder files.

**Step 2: Update router**

```tsx
import { ScriptStudio } from '@/pages/ScriptStudio';
import { WorkflowBuilder } from '@/pages/WorkflowBuilder';
import { SchemaManager } from '@/pages/SchemaManager';
import { FeatureFlags } from '@/pages/FeatureFlags';
import { Chat } from '@/pages/Chat';
import { ApiExplorer } from '@/pages/ApiExplorer';
import { DebugConsole } from '@/pages/DebugConsole';

// Add new routes inside children array:
// Admin mode pages
{ path: 'feature-flags', element: <FeatureFlags /> },
// IDE mode pages
{ path: 'scripts', element: <ScriptStudio /> },
{ path: 'workflow-builder', element: <WorkflowBuilder /> },
{ path: 'schema', element: <SchemaManager /> },
{ path: 'api-explorer', element: <ApiExplorer /> },
{ path: 'debug', element: <DebugConsole /> },
// Assistant mode pages
{ path: 'chat', element: <Chat /> },
```

**Step 3: Build and verify**

```bash
yarn build
```

**Step 4: Commit**

```bash
git add mcp/src/pages/ mcp/src/router/index.tsx
git commit -m "feat: add placeholder pages and routes for IDE modes"
```

---

### Task 4: Rewrite Sidebar with Mode-Based Navigation

**Files:**
- Modify: `mcp/src/components/layout/Sidebar.tsx`

**Step 1: Define navigation per mode**

Replace the single `navigation` array with three mode-specific arrays:

```tsx
import {
  Home, Wrench, History, CreditCard, Settings,
  ChevronLeft, ChevronRight, Compass, GitBranch,
  // New icons:
  Code2, Workflow, Database, Shield, Terminal, Bug,
  MessageSquare, Zap, Star, BookOpen,
} from 'lucide-react';

const adminNav = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Tools', href: '/tools', icon: Wrench },
  { name: 'Workflows', href: '/workflows', icon: GitBranch },
  { name: 'Feature Flags', href: '/feature-flags', icon: Shield },
  { name: 'History', href: '/history', icon: History },
  { name: 'Credits', href: '/credits', icon: CreditCard },
  { name: 'Discovery', href: '/discovery', icon: Compass },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const developerNav = [
  { name: 'Script Studio', href: '/scripts', icon: Code2 },
  { name: 'Workflow Builder', href: '/workflow-builder', icon: Workflow },
  { name: 'Schema Manager', href: '/schema', icon: Database },
  { name: 'API Explorer', href: '/api-explorer', icon: Terminal },
  { name: 'Debug Console', href: '/debug', icon: Bug },
  { name: 'Tools', href: '/tools', icon: Wrench },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const assistantNav = [
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Quick Actions', href: '/tools', icon: Zap },
  { name: 'My Activity', href: '/history', icon: History },
  { name: 'Discovery', href: '/discovery', icon: BookOpen },
  { name: 'Settings', href: '/settings', icon: Settings },
];
```

**Step 2: Use mode from UIStore to select navigation**

```tsx
const { sidebarCollapsed, toggleSidebar, mode } = useUIStore();

const navigation = mode === 'developer' ? developerNav
  : mode === 'assistant' ? assistantNav
  : adminNav;
```

Remove the `hasNextAI` conditional — workflows are now always visible in admin mode.

**Step 3: Add mode label at top of sidebar**

Above the navigation list, add:

```tsx
<div className={cn('px-3 py-2 mb-2', sidebarCollapsed && 'text-center')}>
  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
    {!sidebarCollapsed && (mode === 'developer' ? 'IDE' : mode === 'assistant' ? 'Assistant' : 'Control Panel')}
  </span>
</div>
```

**Step 4: Build and verify**

```bash
yarn build
```

**Step 5: Commit**

```bash
git add mcp/src/components/layout/Sidebar.tsx
git commit -m "feat: mode-based sidebar navigation (admin/developer/assistant)"
```

---

### Task 5: Rewrite TopBar with Three-Mode Switcher

**Files:**
- Modify: `mcp/src/components/layout/TopBar.tsx`

**Step 1: Replace the simple/advanced toggle with a three-mode switcher**

Replace the mode switcher Button (lines 60-73) with:

```tsx
{/* Mode Switcher */}
<div className="hidden md:flex items-center rounded-lg border bg-muted p-0.5">
  {[
    { mode: 'admin' as const, label: 'Admin', icon: Shield },
    { mode: 'developer' as const, label: 'IDE', icon: Code2 },
    { mode: 'assistant' as const, label: 'Chat', icon: MessageSquare },
  ].map(({ mode: m, label, icon: Icon }) => (
    <button
      key={m}
      onClick={() => setMode(m)}
      className={cn(
        'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all',
        mode === m
          ? 'bg-background text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground'
      )}
    >
      <Icon className="size-3.5" />
      {label}
    </button>
  ))}
</div>
```

Add imports for `Shield`, `Code2`, `MessageSquare` from lucide-react and `cn` from utils.

**Step 2: Update the mobile dropdown to show three modes**

Replace the mobile mode toggle DropdownMenuItem (line 93) with three items:

```tsx
{(['admin', 'developer', 'assistant'] as const).map((m) => (
  <DropdownMenuItem
    key={m}
    className="md:hidden"
    onClick={() => setMode(m)}
  >
    {m === 'admin' && <Shield className="mr-2 size-4" />}
    {m === 'developer' && <Code2 className="mr-2 size-4" />}
    {m === 'assistant' && <MessageSquare className="mr-2 size-4" />}
    {m.charAt(0).toUpperCase() + m.slice(1)} Mode
    {mode === m && ' ✓'}
  </DropdownMenuItem>
))}
```

**Step 3: Update the logo/title to reflect the product name**

Change "MCP Tools" to "Frappe AI IDE":

```tsx
<Sparkles className="size-6 text-primary" />
<h1 className="text-xl font-bold">Frappe AI IDE</h1>
```

**Step 4: Build and verify**

```bash
yarn build
```

**Step 5: Commit**

```bash
git add mcp/src/components/layout/TopBar.tsx
git commit -m "feat: three-mode switcher in TopBar (Admin/IDE/Chat)"
```

---

### Task 6: Update AppShell to Show Sidebar in All Modes

**Files:**
- Modify: `mcp/src/components/layout/AppShell.tsx`

**Step 1: Always show sidebar (remove mode === 'advanced' gate)**

Change line 27 from:
```tsx
{mode === 'advanced' && <Sidebar />}
```
to:
```tsx
<Sidebar />
```

The sidebar now always renders — it shows different navigation items per mode (handled in Task 4).

**Step 2: Build and verify**

```bash
yarn build
```

Navigate to each mode — sidebar should show different nav items. All routes should work.

**Step 3: Commit**

```bash
git add mcp/src/components/layout/AppShell.tsx
git commit -m "feat: always show sidebar, navigation adapts per mode"
```

---

### Task 7: Update Settings Page for Three Modes

**Files:**
- Modify: `mcp/src/pages/Settings.tsx`

**Step 1: Update mode radio group to show three modes**

Replace the two-option RadioGroup with three options:

```tsx
<RadioGroup value={mode} onValueChange={(value) => setMode(value as UIMode)}>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="admin" id="admin" />
    <Label htmlFor="admin" className="cursor-pointer">
      <div>
        <p className="font-medium">Control Panel</p>
        <p className="text-sm text-muted-foreground">
          Manage tools, workflows, channels, and access control
        </p>
      </div>
    </Label>
  </div>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="developer" id="developer" />
    <Label htmlFor="developer" className="cursor-pointer">
      <div>
        <p className="font-medium">IDE</p>
        <p className="text-sm text-muted-foreground">
          Script editor, workflow builder, schema manager, API explorer
        </p>
      </div>
    </Label>
  </div>
  <div className="flex items-center space-x-2">
    <RadioGroupItem value="assistant" id="assistant" />
    <Label htmlFor="assistant" className="cursor-pointer">
      <div>
        <p className="font-medium">Assistant</p>
        <p className="text-sm text-muted-foreground">
          Chat interface for natural language interaction
        </p>
      </div>
    </Label>
  </div>
</RadioGroup>
```

**Step 2: Build and verify**

```bash
yarn build
```

**Step 3: Commit**

```bash
git add mcp/src/pages/Settings.tsx
git commit -m "feat: update Settings page for three-mode system"
```

---

## Phase B: Install uselayouts + Backend APIs

### Task 8: Install uselayouts Components

**Files:**
- Multiple new files in `mcp/src/components/ui/`

**Step 1: Install each component via shadcn CLI**

Run each command from `mcp/` directory:

```bash
cd /Users/pavankumarmarwaha/Documents/frappe-bench5/apps/mcp_ui/mcp

# Core components for the IDE
npx shadcn@latest add https://uselayouts.com/r/animated-collection
npx shadcn@latest add https://uselayouts.com/r/bento-card
npx shadcn@latest add https://uselayouts.com/r/vertical-tabs
npx shadcn@latest add https://uselayouts.com/r/filter-interaction
npx shadcn@latest add https://uselayouts.com/r/status-button
npx shadcn@latest add https://uselayouts.com/r/stacked-list
npx shadcn@latest add https://uselayouts.com/r/multi-step-form
npx shadcn@latest add https://uselayouts.com/r/morphing-input
npx shadcn@latest add https://uselayouts.com/r/inline-edit
npx shadcn@latest add https://uselayouts.com/r/delete-button
npx shadcn@latest add https://uselayouts.com/r/discrete-tabs
npx shadcn@latest add https://uselayouts.com/r/fluid-expanding-grid
npx shadcn@latest add https://uselayouts.com/r/dynamic-toolbar
```

**Step 2: Build to verify all components compile**

```bash
yarn build
```

If any component has import issues, fix them (e.g., missing peer dependencies).

**Step 3: Commit**

```bash
git add mcp/src/components/
git commit -m "feat: install uselayouts animated components"
```

---

### Task 9: Add Backend APIs for Script/Workflow/Schema Management

**Files:**
- Create: `mcp_ui/api/ide.py`

**Step 1: Create the IDE API module**

This module wraps Frappe's REST API for IDE operations. All functions use `@frappe.whitelist()`.

```python
"""
IDE API - Script Studio, Workflow Builder, Schema Manager
All operations use standard Frappe API (database-stored, no file access needed)
"""
import frappe
import json


# ──── Capability Detection ────

@frappe.whitelist()
def get_capabilities():
    """Detect what the IDE can do on this site"""
    # Check server scripts
    server_scripts_enabled = False
    try:
        conf = frappe.get_site_config()
        server_scripts_enabled = bool(conf.get("server_script_enabled"))
    except Exception:
        pass

    # Check Script Manager role
    has_script_manager = "Script Manager" in frappe.get_roles()

    return {
        "success": True,
        "server_scripts_enabled": server_scripts_enabled,
        "has_script_manager": has_script_manager,
        "user_roles": frappe.get_roles(),
    }


# ──── Client Scripts ────

@frappe.whitelist()
def get_client_scripts(doctype=None):
    """List all client scripts, optionally filtered by DocType"""
    filters = {}
    if doctype:
        filters["dt"] = doctype

    scripts = frappe.get_all(
        "Client Script",
        filters=filters,
        fields=["name", "dt", "view", "enabled", "module", "modified"],
        order_by="modified desc",
    )
    return {"success": True, "scripts": scripts}


@frappe.whitelist()
def get_client_script(name):
    """Get a single client script with full code"""
    doc = frappe.get_doc("Client Script", name)
    return {
        "success": True,
        "script": {
            "name": doc.name,
            "dt": doc.dt,
            "view": doc.view,
            "enabled": doc.enabled,
            "script": doc.script,
            "module": doc.module,
        },
    }


@frappe.whitelist()
def save_client_script(name=None, dt=None, view="Form", enabled=1, script="", module=None):
    """Create or update a client script"""
    if name and frappe.db.exists("Client Script", name):
        doc = frappe.get_doc("Client Script", name)
        doc.script = script
        doc.enabled = int(enabled)
        doc.save()
    else:
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "name": name or f"{dt} - Custom",
            "dt": dt,
            "view": view,
            "enabled": int(enabled),
            "script": script,
            "module": module,
        })
        doc.insert()

    return {"success": True, "name": doc.name}


@frappe.whitelist()
def delete_client_script(name):
    """Delete a client script"""
    frappe.delete_doc("Client Script", name)
    return {"success": True}


# ──── Server Scripts ────

@frappe.whitelist()
def get_server_scripts(doctype=None, script_type=None):
    """List server scripts"""
    filters = {}
    if doctype:
        filters["reference_doctype"] = doctype
    if script_type:
        filters["script_type"] = script_type

    scripts = frappe.get_all(
        "Server Script",
        filters=filters,
        fields=["name", "script_type", "reference_doctype", "doctype_event",
                "api_method", "disabled", "event_frequency", "modified"],
        order_by="modified desc",
    )
    return {"success": True, "scripts": scripts}


@frappe.whitelist()
def get_server_script(name):
    """Get a single server script with full code"""
    doc = frappe.get_doc("Server Script", name)
    return {
        "success": True,
        "script": {
            "name": doc.name,
            "script_type": doc.script_type,
            "reference_doctype": doc.reference_doctype,
            "doctype_event": doc.doctype_event,
            "api_method": doc.api_method,
            "allow_guest": doc.allow_guest,
            "disabled": doc.disabled,
            "event_frequency": doc.event_frequency,
            "cron_format": doc.cron_format,
            "script": doc.script,
            "module": doc.module,
        },
    }


@frappe.whitelist()
def save_server_script(name=None, script_type=None, reference_doctype=None,
                       doctype_event=None, api_method=None, script="",
                       disabled=0, event_frequency=None, cron_format=None,
                       allow_guest=0, module=None):
    """Create or update a server script"""
    if name and frappe.db.exists("Server Script", name):
        doc = frappe.get_doc("Server Script", name)
        doc.script = script
        doc.disabled = int(disabled)
        doc.save()
    else:
        doc = frappe.get_doc({
            "doctype": "Server Script",
            "name": name,
            "script_type": script_type,
            "reference_doctype": reference_doctype,
            "doctype_event": doctype_event,
            "api_method": api_method,
            "allow_guest": int(allow_guest),
            "disabled": int(disabled),
            "event_frequency": event_frequency,
            "cron_format": cron_format,
            "script": script,
            "module": module,
        })
        doc.insert()

    return {"success": True, "name": doc.name}


# ──── Workflows ────

@frappe.whitelist()
def get_frappe_workflows():
    """Get all Frappe standard workflows"""
    workflows = frappe.get_all(
        "Workflow",
        fields=["name", "workflow_name", "document_type", "is_active", "modified"],
        order_by="modified desc",
    )

    for wf in workflows:
        wf["states"] = frappe.get_all(
            "Workflow Document State",
            filters={"parent": wf["name"]},
            fields=["state", "doc_status", "allow_edit", "update_field", "update_value", "is_optional_state"],
            order_by="idx asc",
        )
        wf["transitions"] = frappe.get_all(
            "Workflow Transition",
            filters={"parent": wf["name"]},
            fields=["state", "action", "next_state", "allowed", "allow_self_approval", "condition"],
            order_by="idx asc",
        )

    return {"success": True, "workflows": workflows}


@frappe.whitelist()
def save_workflow(workflow_name, document_type, is_active=1, states=None, transitions=None):
    """Create or update a Frappe workflow"""
    states = json.loads(states) if isinstance(states, str) else (states or [])
    transitions = json.loads(transitions) if isinstance(transitions, str) else (transitions or [])

    # Ensure workflow states exist
    for s in states:
        if not frappe.db.exists("Workflow State", s.get("state")):
            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s["state"],
            }).insert(ignore_permissions=True)

    # Ensure workflow actions exist
    for t in transitions:
        if not frappe.db.exists("Workflow Action Master", t.get("action")):
            frappe.get_doc({
                "doctype": "Workflow Action Master",
                "workflow_action_name": t["action"],
            }).insert(ignore_permissions=True)

    if frappe.db.exists("Workflow", workflow_name):
        doc = frappe.get_doc("Workflow", workflow_name)
        doc.is_active = int(is_active)
        doc.states = []
        doc.transitions = []
        for s in states:
            doc.append("states", s)
        for t in transitions:
            doc.append("transitions", t)
        doc.save()
    else:
        doc = frappe.get_doc({
            "doctype": "Workflow",
            "workflow_name": workflow_name,
            "document_type": document_type,
            "is_active": int(is_active),
            "states": states,
            "transitions": transitions,
        })
        doc.insert()

    return {"success": True, "name": doc.name}


# ──── Schema Management ────

@frappe.whitelist()
def get_custom_fields_for_doctype(doctype):
    """Get all custom fields for a DocType"""
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": doctype},
        fields=["name", "label", "fieldname", "fieldtype", "options",
                "reqd", "hidden", "read_only", "default", "insert_after",
                "depends_on", "description"],
        order_by="idx asc",
    )
    return {"success": True, "fields": fields}


@frappe.whitelist()
def add_custom_field(dt, label, fieldtype, options=None, insert_after=None,
                     reqd=0, hidden=0, default=None, description=None):
    """Add a custom field to a DocType"""
    doc = frappe.get_doc({
        "doctype": "Custom Field",
        "dt": dt,
        "label": label,
        "fieldtype": fieldtype,
        "options": options,
        "insert_after": insert_after,
        "reqd": int(reqd),
        "hidden": int(hidden),
        "default": default,
        "description": description,
    })
    doc.insert()
    return {"success": True, "name": doc.name, "fieldname": doc.fieldname}


@frappe.whitelist()
def delete_custom_field(name):
    """Delete a custom field"""
    frappe.delete_doc("Custom Field", name)
    return {"success": True}


# ──── Notifications ────

@frappe.whitelist()
def get_notifications():
    """Get all notification rules"""
    notifications = frappe.get_all(
        "Notification",
        fields=["name", "subject", "document_type", "event", "channel",
                "enabled", "modified"],
        order_by="modified desc",
    )
    return {"success": True, "notifications": notifications}
```

**Step 2: Add IDE API methods to the frontend api.ts**

Add to `mcp/src/lib/api.ts` in the FrappeAPI class:

```typescript
// ===== IDE APIs =====

async getCapabilities() {
  return this.call('mcp_ui.api.ide.get_capabilities');
}

async getClientScripts(doctype?: string) {
  return this.call('mcp_ui.api.ide.get_client_scripts', { doctype });
}

async getClientScript(name: string) {
  return this.call('mcp_ui.api.ide.get_client_script', { name });
}

async saveClientScript(data: {
  name?: string; dt?: string; view?: string;
  enabled?: number; script?: string; module?: string;
}) {
  return this.call('mcp_ui.api.ide.save_client_script', data);
}

async deleteClientScript(name: string) {
  return this.call('mcp_ui.api.ide.delete_client_script', { name });
}

async getServerScripts(doctype?: string, scriptType?: string) {
  return this.call('mcp_ui.api.ide.get_server_scripts', {
    doctype, script_type: scriptType,
  });
}

async getServerScript(name: string) {
  return this.call('mcp_ui.api.ide.get_server_script', { name });
}

async saveServerScript(data: {
  name?: string; script_type?: string; reference_doctype?: string;
  doctype_event?: string; api_method?: string; script?: string;
  disabled?: number; event_frequency?: string; cron_format?: string;
  allow_guest?: number; module?: string;
}) {
  return this.call('mcp_ui.api.ide.save_server_script', data);
}

async getFrappeWorkflows() {
  return this.call('mcp_ui.api.ide.get_frappe_workflows');
}

async saveFrappeWorkflow(data: {
  workflow_name: string; document_type: string; is_active?: number;
  states?: any[]; transitions?: any[];
}) {
  return this.call('mcp_ui.api.ide.save_workflow', {
    ...data,
    states: JSON.stringify(data.states),
    transitions: JSON.stringify(data.transitions),
  });
}

async getCustomFieldsForDoctype(doctype: string) {
  return this.call('mcp_ui.api.ide.get_custom_fields_for_doctype', { doctype });
}

async addCustomField(data: {
  dt: string; label: string; fieldtype: string;
  options?: string; insert_after?: string; reqd?: number;
  hidden?: number; default?: string; description?: string;
}) {
  return this.call('mcp_ui.api.ide.add_custom_field', data);
}

async deleteCustomField(name: string) {
  return this.call('mcp_ui.api.ide.delete_custom_field', { name });
}

async getNotifications() {
  return this.call('mcp_ui.api.ide.get_notifications');
}
```

**Step 3: Build and verify**

```bash
yarn build
```

**Step 4: Commit**

```bash
git add mcp_ui/api/ide.py mcp/src/lib/api.ts
git commit -m "feat: add IDE backend APIs (scripts, workflows, schema, notifications)"
```

---

## Phase C: Build IDE Pages

### Task 10: Build Script Studio Page

**Files:**
- Modify: `mcp/src/pages/ScriptStudio.tsx`

Build the Script Studio with two tabs (Client Scripts, Server Scripts), a list view on the left, and a code editor on the right. Use a textarea for the code editor initially (Monaco can be added later).

The Script Studio should:
1. List existing Client Scripts with enable/disable toggles
2. Allow creating new Client Scripts (select DocType, write JS)
3. List Server Scripts with disable toggles
4. Show graceful degradation banner if server scripts are disabled
5. Allow creating new Server Scripts (select type, DocType, event, write Python)

Use Vertical Tabs from uselayouts for the left sidebar tabs.

**Step 1: Implement the full ScriptStudio component**

(Full implementation code — approximately 300 lines covering both tabs, list views, create/edit forms with code textareas, capability detection banner, and API integration via react-query)

**Step 2: Build and verify**

```bash
yarn build
```

Navigate to IDE mode → Script Studio. Verify:
- Client Scripts list loads
- Can create a new Client Script
- Server Scripts tab shows degradation banner if disabled
- Can enable/disable scripts

**Step 3: Commit**

```bash
git add mcp/src/pages/ScriptStudio.tsx
git commit -m "feat: Script Studio page with client/server script management"
```

---

### Task 11: Build Workflow Builder Page

**Files:**
- Modify: `mcp/src/pages/WorkflowBuilder.tsx`

Build the Workflow Builder that:
1. Lists all Frappe workflows (not NextAI funnels) with active/inactive status
2. Shows states and transitions for each workflow
3. Allows creating new workflows with a visual state machine
4. Uses Status Button from uselayouts for workflow status

For the visual state machine, start with a simple table/list representation of states and transitions (a full drag-and-drop editor like reactflow is a future enhancement).

**Step 1: Implement WorkflowBuilder**

(Full implementation — list view with workflow cards, expand to show states/transitions table, create workflow form with dynamic state/transition rows)

**Step 2: Build and verify**

**Step 3: Commit**

---

### Task 12: Build Schema Manager Page

**Files:**
- Modify: `mcp/src/pages/SchemaManager.tsx`

Build the Schema Manager that:
1. Shows DocTypes in a searchable grid
2. Click a DocType to see its fields (both standard and custom)
3. Add/remove Custom Fields from the UI
4. Uses Filter Interaction from uselayouts for module filtering

**Step 1: Implement SchemaManager**

**Step 2: Build and verify**

**Step 3: Commit**

---

### Task 13: Build Feature Flags Page

**Files:**
- Modify: `mcp/src/pages/FeatureFlags.tsx`
- Create: `mcp_ui/api/feature_flags.py`

Build the Feature Flags management page that:
1. Shows per-DocType toggle matrix (read/create/update/delete/scripts/workflows/fields)
2. Shows per-tool enable/disable
3. Shows channel toggles
4. Uses Discrete Tabs from uselayouts for categories

Backend stores flags in MCP Settings (or a new DocType if needed).

**Step 1: Create backend API for feature flags**

**Step 2: Implement FeatureFlags page**

**Step 3: Build and verify**

**Step 4: Commit**

---

### Task 14: Build Chat/Assistant Page

**Files:**
- Modify: `mcp/src/pages/Chat.tsx`

Build a chat-style interface that:
1. Shows a message thread UI
2. User types natural language
3. Uses the existing NLP parser (ai_nlp or nlp_processor) to interpret
4. Shows AI responses with tool execution results
5. Uses Morphing Input from uselayouts for the chat input

**Step 1: Implement Chat page**

**Step 2: Build and verify**

**Step 3: Commit**

---

### Task 15: Build API Explorer Page

**Files:**
- Modify: `mcp/src/pages/ApiExplorer.tsx`

Build an API testing interface that:
1. Lists all available MCP tools
2. Click a tool to see its schema
3. Fill in parameters and execute
4. Shows raw request/response JSON
5. Reuses ToolExecutor logic but with developer-focused display

**Step 1: Implement ApiExplorer**

**Step 2: Build and verify**

**Step 3: Commit**

---

## Phase D: Polish Existing Pages with uselayouts

### Task 16: Rewrite Dashboard with Bento Cards

**Files:**
- Modify: `mcp/src/pages/Dashboard.tsx`

Replace the current hero section and card grid with:
1. Bento Cards for metrics (Active DocTypes, Scripts Running, Workflows Active, AI Ops Today)
2. Animated Collection for recent activity
3. Keep NLP input for assistant mode

**Step 1: Implement new Dashboard**

**Step 2: Build and verify**

**Step 3: Commit**

---

### Task 17: Rewrite Tools with Animated Collection + Multi-Step Form

**Files:**
- Modify: `mcp/src/pages/Tools.tsx`
- Modify: `mcp/src/components/tools/ToolExecutor.tsx`

Replace the tool grid with:
1. Animated Collection (switchable List/Card/Pack views)
2. Filter Interaction for category filtering
3. Tool execution via Multi-Step Form wizard (Step 1: select DocType, Step 2: fill fields, Step 3: review & execute)

**Step 1: Implement new Tools page**

**Step 2: Implement Multi-Step Form tool execution**

**Step 3: Build and verify**

**Step 4: Commit**

---

## Phase E: Integration Testing

### Task 18: End-to-End Testing with Playwright

Use Playwright MCP tools to test every page in every mode:

1. **Admin mode:** Dashboard → Tools → Execute a tool → History shows result
2. **IDE mode:** Script Studio → Create Client Script → Verify it appears in Frappe
3. **IDE mode:** Workflow Builder → Create Workflow → Verify states and transitions
4. **IDE mode:** Schema Manager → Add Custom Field → Verify field added
5. **Assistant mode:** Chat → "Show all customers" → Verify NLP response
6. **Cross-mode:** Switch between modes → Verify sidebar changes
7. **Feature Flags:** Toggle a DocType flag → Verify it affects tool execution
8. **Console errors:** Check zero JS errors on every page

Fix any bugs found.

---

### Task 19: Final Commit and Build

```bash
yarn build
git add -A
git commit -m "feat: Frappe AI IDE — three-mode command center with Script Studio, Workflow Builder, Schema Manager, and uselayouts animations"
```

---

## File Map

| File | Action | Task |
|------|--------|------|
| `mcp/src/components/tools/SmartForm.tsx` | Modify | 1 |
| `mcp/src/types/index.ts` | Modify | 2 |
| `mcp/src/stores/uiStore.ts` | Modify | 2 |
| `mcp/src/router/index.tsx` | Modify | 3 |
| `mcp/src/pages/ScriptStudio.tsx` | Create | 3, 10 |
| `mcp/src/pages/WorkflowBuilder.tsx` | Create | 3, 11 |
| `mcp/src/pages/SchemaManager.tsx` | Create | 3, 12 |
| `mcp/src/pages/FeatureFlags.tsx` | Create | 3, 13 |
| `mcp/src/pages/Chat.tsx` | Create | 3, 14 |
| `mcp/src/pages/ApiExplorer.tsx` | Create | 3, 15 |
| `mcp/src/pages/DebugConsole.tsx` | Create | 3 |
| `mcp/src/components/layout/Sidebar.tsx` | Modify | 4 |
| `mcp/src/components/layout/TopBar.tsx` | Modify | 5 |
| `mcp/src/components/layout/AppShell.tsx` | Modify | 6 |
| `mcp/src/pages/Settings.tsx` | Modify | 7 |
| `mcp/src/components/ui/` (uselayouts) | Create | 8 |
| `mcp_ui/api/ide.py` | Create | 9 |
| `mcp/src/lib/api.ts` | Modify | 9 |
| `mcp/src/pages/Dashboard.tsx` | Modify | 16 |
| `mcp/src/pages/Tools.tsx` | Modify | 17 |
| `mcp/src/components/tools/ToolExecutor.tsx` | Modify | 17 |
| `mcp_ui/api/feature_flags.py` | Create | 13 |
