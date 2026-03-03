/**
 * Feature Flags Page
 * Granular feature toggles for the MCP UI system
 * Stored in localStorage via zustand, controls which features are visible
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useUIStore } from '@/stores/uiStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Shield, Code2, MessageSquare, Wrench, GitBranch,
  Database, Terminal, Bug, Zap, CreditCard, Compass,
  RefreshCw, RotateCcw, Info, FileCode, Server, Bell,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

// ── Feature Flag Store ─────────────────────────────────────────────
interface FeatureFlagState {
  flags: Record<string, boolean>;
  setFlag: (key: string, value: boolean) => void;
  resetAll: () => void;
}

const DEFAULT_FLAGS: Record<string, boolean> = {
  // Admin features
  'admin.tools': true,
  'admin.workflows': true,
  'admin.feature_flags': true,
  'admin.history': true,
  'admin.credits': true,
  'admin.discovery': true,
  'admin.bulk_operations': true,
  'admin.notifications': true,
  // Developer features
  'dev.client_scripts': true,
  'dev.server_scripts': true,
  'dev.workflow_builder': true,
  'dev.schema_manager': true,
  'dev.api_explorer': true,
  'dev.debug_console': true,
  'dev.doc_events': true,
  'dev.property_setters': true,
  // Assistant features
  'assistant.chat': true,
  'assistant.nlp_input': true,
  'assistant.quick_actions': true,
  'assistant.auto_execute': false,
  // Global
  'global.dark_mode': true,
  'global.keyboard_shortcuts': true,
  'global.confetti_on_success': true,
};

export const useFeatureFlags = create<FeatureFlagState>()(
  persist(
    (set) => ({
      flags: { ...DEFAULT_FLAGS },
      setFlag: (key, value) =>
        set((state) => ({ flags: { ...state.flags, [key]: value } })),
      resetAll: () => set({ flags: { ...DEFAULT_FLAGS } }),
    }),
    { name: 'mcp-ui-feature-flags' }
  )
);

// ── Types ──────────────────────────────────────────────────────────
interface FlagItem {
  key: string;
  label: string;
  description: string;
  icon: LucideIcon;
  requiresServerScripts?: boolean;
}

interface FlagGroup {
  title: string;
  description: string;
  icon: LucideIcon;
  variant: 'default' | 'secondary' | 'outline';
  items: FlagItem[];
}

const FLAG_GROUPS: FlagGroup[] = [
  {
    title: 'Admin Features',
    description: 'Control Panel tools and capabilities',
    icon: Shield,
    variant: 'default',
    items: [
      { key: 'admin.tools', label: 'MCP Tools', description: 'Execute MCP tools from the UI', icon: Wrench },
      { key: 'admin.workflows', label: 'Workflow Automation', description: 'NextAI Funnel workflows', icon: GitBranch },
      { key: 'admin.feature_flags', label: 'Feature Flags', description: 'This page — manage feature toggles', icon: Shield },
      { key: 'admin.history', label: 'Execution History', description: 'View tool execution logs', icon: Zap },
      { key: 'admin.credits', label: 'Credits System', description: 'Credit balance and purchases', icon: CreditCard },
      { key: 'admin.discovery', label: 'System Discovery', description: 'Explore installed apps and DocTypes', icon: Compass },
      { key: 'admin.bulk_operations', label: 'Bulk Operations', description: 'Bulk create, update, delete documents', icon: Database },
      { key: 'admin.notifications', label: 'Notifications', description: 'View notification rules', icon: Bell },
    ],
  },
  {
    title: 'Developer Features',
    description: 'IDE tools and script management',
    icon: Code2,
    variant: 'secondary',
    items: [
      { key: 'dev.client_scripts', label: 'Client Scripts', description: 'Create and edit Client Scripts', icon: FileCode },
      { key: 'dev.server_scripts', label: 'Server Scripts', description: 'Create and edit Server Scripts', icon: Server, requiresServerScripts: true },
      { key: 'dev.workflow_builder', label: 'Workflow Builder', description: 'Build Frappe Workflows', icon: GitBranch },
      { key: 'dev.schema_manager', label: 'Schema Manager', description: 'Custom Fields and Property Setters', icon: Database },
      { key: 'dev.api_explorer', label: 'API Explorer', description: 'Test Frappe REST API calls', icon: Terminal },
      { key: 'dev.debug_console', label: 'Debug Console', description: 'System diagnostics and hooks', icon: Bug },
      { key: 'dev.doc_events', label: 'Doc Events', description: 'View registered doc_events hooks', icon: Zap },
      { key: 'dev.property_setters', label: 'Property Setters', description: 'Override field/DocType properties', icon: Wrench },
    ],
  },
  {
    title: 'Assistant Features',
    description: 'Chat and natural language capabilities',
    icon: MessageSquare,
    variant: 'outline',
    items: [
      { key: 'assistant.chat', label: 'Chat Interface', description: 'Natural language conversation', icon: MessageSquare },
      { key: 'assistant.nlp_input', label: 'NLP Input', description: 'Natural language tool parsing on Dashboard', icon: Zap },
      { key: 'assistant.quick_actions', label: 'Quick Actions', description: 'One-click common operations', icon: Wrench },
      { key: 'assistant.auto_execute', label: 'Auto-Execute', description: 'Automatically run high-confidence parsed actions (caution)', icon: Zap },
    ],
  },
  {
    title: 'Global Settings',
    description: 'System-wide preferences',
    icon: Wrench,
    variant: 'default',
    items: [
      { key: 'global.dark_mode', label: 'Dark Mode', description: 'Allow dark theme toggle', icon: Wrench },
      { key: 'global.keyboard_shortcuts', label: 'Keyboard Shortcuts', description: 'Enable keyboard navigation', icon: Wrench },
      { key: 'global.confetti_on_success', label: 'Confetti Effect', description: 'Show confetti on successful tool execution', icon: Zap },
    ],
  },
];

// ── Main Page ──────────────────────────────────────────────────────
export function FeatureFlags() {
  const { flags, setFlag, resetAll } = useFeatureFlags();
  const { serverScriptsEnabled } = useUIStore();

  // Fetch capabilities for display
  const { data: capabilities, isLoading } = useQuery({
    queryKey: ['capabilities'],
    queryFn: async () => {
      const res = await api.getCapabilities();
      return res;
    },
  });

  const enabledCount = Object.values(flags).filter(Boolean).length;
  const totalCount = Object.keys(flags).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Shield className="size-8 text-primary" />
            Feature Flags
          </h1>
          <p className="mt-2 text-muted-foreground">
            Control which features are available in each mode
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="text-sm px-3 py-1">
            {enabledCount}/{totalCount} enabled
          </Badge>
          <Button variant="outline" size="sm" onClick={resetAll}>
            <RotateCcw className="mr-2 size-3" /> Reset All
          </Button>
        </div>
      </div>

      {/* Capability Status */}
      {isLoading ? (
        <Skeleton className="h-20" />
      ) : capabilities && (
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-wrap gap-3">
              <Badge variant={capabilities.server_scripts_enabled ? 'default' : 'secondary'}>
                Server Scripts: {capabilities.server_scripts_enabled ? 'Enabled' : 'Disabled'}
              </Badge>
              <Badge variant={capabilities.has_script_manager ? 'default' : 'secondary'}>
                Script Manager: {capabilities.has_script_manager ? 'Yes' : 'No'}
              </Badge>
              <Badge variant="outline">
                Roles: {capabilities.user_roles?.length || 0}
              </Badge>
            </div>
            {!capabilities.server_scripts_enabled && (
              <Alert className="mt-3">
                <Info className="size-4" />
                <AlertDescription>
                  Server Scripts are disabled. Features marked with a warning need
                  <code className="mx-1 rounded bg-muted px-1 py-0.5 text-xs">server_script_enabled: 1</code>
                  in site config.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Flag Groups */}
      {FLAG_GROUPS.map((group) => (
        <Card key={group.title}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <group.icon className="size-5" />
              {group.title}
            </CardTitle>
            <CardDescription>{group.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {group.items.map((item) => {
                const disabled = item.requiresServerScripts && !serverScriptsEnabled;
                return (
                  <div
                    key={item.key}
                    className={`flex items-center justify-between rounded-lg border p-3 ${
                      disabled ? 'opacity-60' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="size-4 text-muted-foreground" />
                      <div>
                        <div className="flex items-center gap-2">
                          <Label className="font-medium">{item.label}</Label>
                          {disabled && (
                            <Badge variant="destructive" className="text-[10px]">
                              Requires Server Scripts
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">{item.description}</p>
                      </div>
                    </div>
                    <Switch
                      checked={flags[item.key] ?? false}
                      onCheckedChange={(checked) => setFlag(item.key, checked)}
                      disabled={disabled}
                    />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
