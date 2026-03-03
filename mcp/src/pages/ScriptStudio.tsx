/**
 * Script Studio Page
 * Full-featured editor for Client Scripts and Server Scripts
 * with capability detection (graceful degradation when server scripts disabled)
 */
import { useState, lazy, Suspense } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useUIStore } from '@/stores/uiStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import {
  Code2, Plus, Save, Trash2, Search, AlertTriangle,
  FileCode, Server, Zap, BookTemplate,
} from 'lucide-react';

// Lazy-load Monaco Editor (loads from CDN, doesn't bloat bundle)
const MonacoEditor = lazy(() => import('@monaco-editor/react').then(m => ({ default: m.default })));

// ── Script Templates ─────────────────────────────────────────────────
const CLIENT_TEMPLATES = [
  {
    name: 'Form Validation',
    code: `frappe.ui.form.on('{{DocType}}', {
  validate(frm) {
    if (!frm.doc.customer) {
      frappe.throw(__('Customer is required'));
    }
  }
});`,
  },
  {
    name: 'Set Query Filter',
    code: `frappe.ui.form.on('{{DocType}}', {
  setup(frm) {
    frm.set_query('item_code', () => {
      return {
        filters: {
          disabled: 0,
          is_stock_item: 1
        }
      };
    });
  }
});`,
  },
  {
    name: 'Custom Button',
    code: `frappe.ui.form.on('{{DocType}}', {
  refresh(frm) {
    if (frm.doc.docstatus === 1) {
      frm.add_custom_button(__('Custom Action'), () => {
        frappe.call({
          method: 'my_app.api.custom_action',
          args: { name: frm.doc.name },
          callback(r) {
            if (r.message) {
              frappe.msgprint(r.message);
              frm.reload_doc();
            }
          }
        });
      }, __('Actions'));
    }
  }
});`,
  },
  {
    name: 'List View Button',
    code: `frappe.listview_settings['{{DocType}}'] = {
  onload(listview) {
    listview.page.add_inner_button(__('Bulk Update'), () => {
      const selected = listview.get_checked_items();
      if (!selected.length) {
        frappe.throw(__('Select at least one record'));
      }
      // Process selected items
      frappe.call({
        method: 'my_app.api.bulk_update',
        args: { names: selected.map(d => d.name) },
        callback() {
          listview.refresh();
        }
      });
    });
  }
};`,
  },
];

const SERVER_TEMPLATES = [
  {
    name: 'Before Save Validation',
    code: `# Server Script: DocType Event → Before Save
# Access the document via doc

if not doc.customer_name:
    frappe.throw("Customer Name is required")

# Auto-calculate a field
doc.total_amount = sum(row.amount for row in doc.items)`,
  },
  {
    name: 'API Endpoint',
    code: `# Server Script: API
# Access via /api/method/{{method_name}}
# Use frappe.form_dict for request params

data = frappe.form_dict
doctype = data.get('doctype')
filters = data.get('filters', {})

result = frappe.get_list(
    doctype,
    filters=filters,
    fields=['name', 'status', 'modified'],
    limit_page_length=20
)

frappe.response['message'] = result`,
  },
  {
    name: 'Scheduled Job',
    code: `# Server Script: Scheduler Event
# Runs on schedule (Daily, Hourly, etc.)

import frappe
from frappe.utils import add_days, nowdate

# Find overdue items
overdue = frappe.get_all(
    'ToDo',
    filters={
        'status': 'Open',
        'date': ['<', nowdate()]
    },
    fields=['name', 'owner', 'description']
)

for todo in overdue:
    frappe.sendmail(
        recipients=[todo.owner],
        subject='Overdue ToDo: ' + todo.description[:50],
        message=f'Your ToDo "{todo.description}" is overdue.'
    )`,
  },
  {
    name: 'Permission Query',
    code: `# Server Script: Permission Query
# Restrict which records a user can see

conditions = ""

if not frappe.session.user == "Administrator":
    conditions = f"owner = '{frappe.session.user}'"`,
  },
];

// ── Code Editor Wrapper ──────────────────────────────────────────────
function CodeEditor({
  value,
  onChange,
  language = 'javascript',
  height = '400px',
}: {
  value: string;
  onChange: (val: string) => void;
  language?: string;
  height?: string;
}) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Suspense fallback={
        <div className="flex items-center justify-center bg-[#1e1e1e]" style={{ height }}>
          <span className="text-sm text-zinc-400">Loading editor...</span>
        </div>
      }>
        <MonacoEditor
          height={height}
          language={language}
          value={value}
          onChange={(v) => onChange(v || '')}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineHeight: 20,
            padding: { top: 12, bottom: 12 },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            tabSize: 2,
            automaticLayout: true,
            suggestOnTriggerCharacters: true,
            quickSuggestions: true,
            bracketPairColorization: { enabled: true },
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            renderLineHighlight: 'all',
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
            fontLigatures: true,
          }}
        />
      </Suspense>
    </div>
  );
}

// ── Client Script Editor ───────────────────────────────────────────
interface ClientScript {
  name: string;
  dt: string;
  view: string;
  enabled: number;
  script: string;
  module: string;
  modified: string;
}

function ClientScriptsTab() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: '', dt: '', view: 'Form', enabled: 1, script: '', module: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['client-scripts'],
    queryFn: async () => {
      const res = await api.getClientScripts();
      return res.scripts as ClientScript[];
    },
  });

  const loadScript = useQuery({
    queryKey: ['client-script', selected],
    queryFn: async () => {
      if (!selected) return null;
      const res = await api.getClientScript(selected);
      return res.script as ClientScript;
    },
    enabled: !!selected,
  });

  // When a script is loaded, populate the form
  const handleSelect = (name: string) => {
    setSelected(name);
    setEditing(true);
    // Form will be populated via useEffect-like pattern below
  };

  // Sync loaded script data to form
  if (loadScript.data && editing && loadScript.data.name === selected) {
    const s = loadScript.data;
    if (form.name !== s.name) {
      setForm({
        name: s.name, dt: s.dt, view: s.view,
        enabled: s.enabled, script: s.script, module: s.module || '',
      });
    }
  }

  const saveMutation = useMutation({
    mutationFn: (data: typeof form) => api.saveClientScript(data),
    onSuccess: (res) => {
      toast.success(res.message || 'Client Script saved');
      queryClient.invalidateQueries({ queryKey: ['client-scripts'] });
      if (res.name) {
        setSelected(res.name);
        setForm((prev) => ({ ...prev, name: res.name }));
      }
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteClientScript(name),
    onSuccess: () => {
      toast.success('Client Script deleted');
      queryClient.invalidateQueries({ queryKey: ['client-scripts'] });
      handleNewScript();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const handleNewScript = () => {
    setSelected(null);
    setEditing(true);
    setForm({ name: '', dt: '', view: 'Form', enabled: 1, script: '', module: '' });
  };

  const filtered = data?.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.dt.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Script List */}
      <Card className="lg:col-span-1">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Scripts</CardTitle>
            <Button size="sm" variant="outline" onClick={handleNewScript}>
              <Plus className="mr-1 size-3" /> New
            </Button>
          </div>
          <div className="relative mt-2">
            <Search className="absolute left-2 top-2.5 size-4 text-muted-foreground" />
            <Input
              placeholder="Search scripts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[500px]">
            {isLoading ? (
              <div className="space-y-2 p-4">
                {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}
              </div>
            ) : filtered.length === 0 ? (
              <p className="p-4 text-center text-sm text-muted-foreground">No scripts found</p>
            ) : (
              <div className="divide-y">
                {filtered.map((s) => (
                  <button
                    key={s.name}
                    onClick={() => handleSelect(s.name)}
                    className={`w-full px-4 py-3 text-left hover:bg-accent transition-colors ${
                      selected === s.name ? 'bg-accent' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium truncate">{s.name}</span>
                      <Badge variant={s.enabled ? 'default' : 'secondary'} className="text-[10px]">
                        {s.enabled ? 'ON' : 'OFF'}
                      </Badge>
                    </div>
                    <div className="flex gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">{s.dt}</span>
                      <span className="text-xs text-muted-foreground">· {s.view}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Editor */}
      <Card className="lg:col-span-2">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileCode className="size-4" />
              {form.name || 'New Client Script'}
            </CardTitle>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => saveMutation.mutate(form)}
                disabled={!form.dt || !form.script || saveMutation.isPending}
              >
                <Save className="mr-1 size-3" />
                {saveMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
              {form.name && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => {
                    if (confirm(`Delete "${form.name}"?`)) {
                      deleteMutation.mutate(form.name);
                    }
                  }}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="size-3" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {!editing ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <p>Select a script or create a new one</p>
            </div>
          ) : loadScript.isLoading && selected ? (
            <div className="space-y-4">
              <Skeleton className="h-10" />
              <Skeleton className="h-64" />
            </div>
          ) : (
            <>
              {/* Metadata Row */}
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <Label>DocType</Label>
                  <Input
                    value={form.dt}
                    onChange={(e) => setForm({ ...form, dt: e.target.value })}
                    placeholder="e.g. Sales Order"
                  />
                </div>
                <div>
                  <Label>View</Label>
                  <select
                    value={form.view}
                    onChange={(e) => setForm({ ...form, view: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="Form">Form</option>
                    <option value="List">List</option>
                    <option value="Report">Report</option>
                    <option value="Calendar">Calendar</option>
                  </select>
                </div>
                <div className="flex items-end gap-3">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={!!form.enabled}
                      onCheckedChange={(checked) => setForm({ ...form, enabled: checked ? 1 : 0 })}
                    />
                    <Label>{form.enabled ? 'Enabled' : 'Disabled'}</Label>
                  </div>
                </div>
              </div>

              {/* Templates */}
              {!form.script && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-1.5">
                    <Zap className="size-3 text-primary" /> Quick Templates
                  </Label>
                  <div className="flex flex-wrap gap-1.5">
                    {CLIENT_TEMPLATES.map(t => (
                      <button
                        key={t.name}
                        onClick={() => setForm({ ...form, script: t.code.replace(/\{\{DocType\}\}/g, form.dt || 'MyDocType') })}
                        className="rounded-lg border bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                      >
                        {t.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Monaco Code Editor */}
              <div>
                <Label>Script</Label>
                <CodeEditor
                  value={form.script}
                  onChange={(val) => setForm({ ...form, script: val })}
                  language="javascript"
                  height="400px"
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Server Script Editor ───────────────────────────────────────────
interface ServerScript {
  name: string;
  script_type: string;
  reference_doctype: string;
  doctype_event: string;
  api_method: string;
  script: string;
  disabled: number;
  event_frequency: string;
  cron_format: string;
  allow_guest: number;
  module: string;
  modified: string;
}

const SCRIPT_TYPES = [
  'DocType Event', 'Scheduler Event', 'Permission Query', 'API',
];

const DOCTYPE_EVENTS = [
  'Before Insert', 'Before Validate', 'Before Save', 'After Insert',
  'After Save', 'Before Submit', 'After Submit', 'Before Cancel',
  'After Cancel', 'Before Delete', 'After Delete', 'On Change',
];

const EVENT_FREQUENCIES = [
  'All', 'Hourly', 'Hourly Long', 'Daily', 'Daily Long',
  'Weekly', 'Weekly Long', 'Monthly', 'Monthly Long', 'Cron',
];

function ServerScriptsTab() {
  const { serverScriptsEnabled } = useUIStore();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: '', script_type: 'DocType Event', reference_doctype: '',
    doctype_event: 'Before Save', api_method: '', script: '',
    disabled: 0, event_frequency: 'Daily', cron_format: '',
    allow_guest: 0, module: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['server-scripts'],
    queryFn: async () => {
      const res = await api.getServerScripts();
      return res.scripts as ServerScript[];
    },
    enabled: serverScriptsEnabled,
  });

  const loadScript = useQuery({
    queryKey: ['server-script', selected],
    queryFn: async () => {
      if (!selected) return null;
      const res = await api.getServerScript(selected);
      return res.script as ServerScript;
    },
    enabled: !!selected && serverScriptsEnabled,
  });

  const handleSelect = (name: string) => {
    setSelected(name);
    setEditing(true);
  };

  // Sync loaded script data to form
  if (loadScript.data && editing && loadScript.data.name === selected) {
    const s = loadScript.data;
    if (form.name !== s.name) {
      setForm({
        name: s.name, script_type: s.script_type, reference_doctype: s.reference_doctype || '',
        doctype_event: s.doctype_event || '', api_method: s.api_method || '',
        script: s.script, disabled: s.disabled, event_frequency: s.event_frequency || 'Daily',
        cron_format: s.cron_format || '', allow_guest: s.allow_guest, module: s.module || '',
      });
    }
  }

  const saveMutation = useMutation({
    mutationFn: (data: typeof form) => api.saveServerScript(data),
    onSuccess: (res) => {
      toast.success(res.message || 'Server Script saved');
      queryClient.invalidateQueries({ queryKey: ['server-scripts'] });
      if (res.name) {
        setSelected(res.name);
        setForm((prev) => ({ ...prev, name: res.name }));
      }
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteServerScript(name),
    onSuccess: () => {
      toast.success('Server Script deleted');
      queryClient.invalidateQueries({ queryKey: ['server-scripts'] });
      handleNewScript();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const handleNewScript = () => {
    setSelected(null);
    setEditing(true);
    setForm({
      name: '', script_type: 'DocType Event', reference_doctype: '',
      doctype_event: 'Before Save', api_method: '', script: '',
      disabled: 0, event_frequency: 'Daily', cron_format: '',
      allow_guest: 0, module: '',
    });
  };

  if (!serverScriptsEnabled) {
    return (
      <Alert>
        <AlertTriangle className="size-4" />
        <AlertDescription>
          <strong>Server Scripts are disabled.</strong> To enable, add{' '}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">server_script_enabled: 1</code>{' '}
          to your site config (<code className="text-xs">common_site_config.json</code>) and restart bench.
          <br />
          <span className="text-muted-foreground mt-1 block">
            Client Scripts, Workflows, and Custom Fields still work normally without this setting.
          </span>
        </AlertDescription>
      </Alert>
    );
  }

  const filtered = data?.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      (s.reference_doctype || '').toLowerCase().includes(search.toLowerCase()) ||
      s.script_type.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Script List */}
      <Card className="lg:col-span-1">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Scripts</CardTitle>
            <Button size="sm" variant="outline" onClick={handleNewScript}>
              <Plus className="mr-1 size-3" /> New
            </Button>
          </div>
          <div className="relative mt-2">
            <Search className="absolute left-2 top-2.5 size-4 text-muted-foreground" />
            <Input
              placeholder="Search scripts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[500px]">
            {isLoading ? (
              <div className="space-y-2 p-4">
                {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}
              </div>
            ) : filtered.length === 0 ? (
              <p className="p-4 text-center text-sm text-muted-foreground">No scripts found</p>
            ) : (
              <div className="divide-y">
                {filtered.map((s) => (
                  <button
                    key={s.name}
                    onClick={() => handleSelect(s.name)}
                    className={`w-full px-4 py-3 text-left hover:bg-accent transition-colors ${
                      selected === s.name ? 'bg-accent' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium truncate">{s.name}</span>
                      <Badge variant={s.disabled ? 'secondary' : 'default'} className="text-[10px]">
                        {s.disabled ? 'OFF' : 'ON'}
                      </Badge>
                    </div>
                    <div className="flex gap-2 mt-1">
                      <Badge variant="outline" className="text-[10px]">{s.script_type}</Badge>
                      {s.reference_doctype && (
                        <span className="text-xs text-muted-foreground">{s.reference_doctype}</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Editor */}
      <Card className="lg:col-span-2">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Server className="size-4" />
              {form.name || 'New Server Script'}
            </CardTitle>
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => saveMutation.mutate(form)}
                disabled={!form.script || saveMutation.isPending}
              >
                <Save className="mr-1 size-3" />
                {saveMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
              {form.name && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => {
                    if (confirm(`Delete "${form.name}"?`)) {
                      deleteMutation.mutate(form.name);
                    }
                  }}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="size-3" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {!editing ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              <p>Select a script or create a new one</p>
            </div>
          ) : loadScript.isLoading && selected ? (
            <div className="space-y-4">
              <Skeleton className="h-10" />
              <Skeleton className="h-64" />
            </div>
          ) : (
            <>
              {/* Metadata */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label>Script Type</Label>
                  <select
                    value={form.script_type}
                    onChange={(e) => setForm({ ...form, script_type: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {SCRIPT_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>

                {form.script_type === 'DocType Event' && (
                  <>
                    <div>
                      <Label>DocType</Label>
                      <Input
                        value={form.reference_doctype}
                        onChange={(e) => setForm({ ...form, reference_doctype: e.target.value })}
                        placeholder="e.g. Sales Order"
                      />
                    </div>
                    <div>
                      <Label>Event</Label>
                      <select
                        value={form.doctype_event}
                        onChange={(e) => setForm({ ...form, doctype_event: e.target.value })}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        {DOCTYPE_EVENTS.map((e) => (
                          <option key={e} value={e}>{e}</option>
                        ))}
                      </select>
                    </div>
                  </>
                )}

                {form.script_type === 'API' && (
                  <div>
                    <Label>API Method</Label>
                    <Input
                      value={form.api_method}
                      onChange={(e) => setForm({ ...form, api_method: e.target.value })}
                      placeholder="e.g. my_app.api.my_method"
                    />
                  </div>
                )}

                {form.script_type === 'Scheduler Event' && (
                  <>
                    <div>
                      <Label>Frequency</Label>
                      <select
                        value={form.event_frequency}
                        onChange={(e) => setForm({ ...form, event_frequency: e.target.value })}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        {EVENT_FREQUENCIES.map((f) => (
                          <option key={f} value={f}>{f}</option>
                        ))}
                      </select>
                    </div>
                    {form.event_frequency === 'Cron' && (
                      <div>
                        <Label>Cron Format</Label>
                        <Input
                          value={form.cron_format}
                          onChange={(e) => setForm({ ...form, cron_format: e.target.value })}
                          placeholder="*/5 * * * *"
                        />
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Toggles Row */}
              <div className="flex gap-6">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={!form.disabled}
                    onCheckedChange={(checked) => setForm({ ...form, disabled: checked ? 0 : 1 })}
                  />
                  <Label>{form.disabled ? 'Disabled' : 'Enabled'}</Label>
                </div>
                {form.script_type === 'API' && (
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={!!form.allow_guest}
                      onCheckedChange={(checked) => setForm({ ...form, allow_guest: checked ? 1 : 0 })}
                    />
                    <Label>Allow Guest</Label>
                  </div>
                )}
              </div>

              {/* Templates */}
              {!form.script && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-1.5">
                    <Zap className="size-3 text-primary" /> Quick Templates
                  </Label>
                  <div className="flex flex-wrap gap-1.5">
                    {SERVER_TEMPLATES.map(t => (
                      <button
                        key={t.name}
                        onClick={() => setForm({ ...form, script: t.code.replace(/\{\{method_name\}\}/g, form.api_method || 'my_method') })}
                        className="rounded-lg border bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
                      >
                        {t.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Monaco Code Editor */}
              <div>
                <Label>Script</Label>
                <CodeEditor
                  value={form.script}
                  onChange={(val) => setForm({ ...form, script: val })}
                  language="python"
                  height="350px"
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────
export function ScriptStudio() {
  const { serverScriptsEnabled, hasScriptManagerRole } = useUIStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Code2 className="size-8 text-primary" />
          Script Studio
        </h1>
        <p className="mt-2 text-muted-foreground">
          Create and manage Client Scripts and Server Scripts
        </p>
      </div>

      {/* Capability Badges */}
      <div className="flex flex-wrap gap-2">
        <Badge variant="default">
          <FileCode className="mr-1 size-3" /> Client Scripts
        </Badge>
        <Badge variant={serverScriptsEnabled ? 'default' : 'secondary'}>
          <Server className="mr-1 size-3" />
          Server Scripts: {serverScriptsEnabled ? 'Enabled' : 'Disabled'}
        </Badge>
        {!hasScriptManagerRole && (
          <Badge variant="destructive">
            Script Manager role required for Server Scripts
          </Badge>
        )}
      </div>

      <Tabs defaultValue="client">
        <TabsList>
          <TabsTrigger value="client" className="flex items-center gap-2">
            <FileCode className="size-4" /> Client Scripts
          </TabsTrigger>
          <TabsTrigger value="server" className="flex items-center gap-2">
            <Server className="size-4" /> Server Scripts
          </TabsTrigger>
        </TabsList>

        <TabsContent value="client" className="mt-4">
          <ClientScriptsTab />
        </TabsContent>

        <TabsContent value="server" className="mt-4">
          <ServerScriptsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
