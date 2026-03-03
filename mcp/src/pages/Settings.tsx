/**
 * Settings Page
 * Animated vertical tabs layout using uselayouts pattern
 */
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/uiStore';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Shield,
  Code2,
  MessageSquare,
  Info,
  Sun,
  Moon,
  Monitor,
  Palette,
  UserCog,
  CheckCircle2,
  Bot,
  Send,
  RefreshCw,
  Copy,
  Plus,
  Trash2,
  Loader2,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import type { UIMode } from '@/types';

const modeOptions: { value: UIMode; label: string; description: string; icon: typeof Shield }[] = [
  {
    value: 'admin',
    label: 'Control Panel',
    description: 'Manage tools, workflows, channels, feature flags, and access control',
    icon: Shield,
  },
  {
    value: 'developer',
    label: 'IDE',
    description: 'Script editor, workflow builder, schema manager, API explorer, and debug console',
    icon: Code2,
  },
  {
    value: 'assistant',
    label: 'Assistant',
    description: 'Chat interface for natural language interaction with your Frappe system',
    icon: MessageSquare,
  },
];

const themeOptions: { value: 'light' | 'dark' | 'system'; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

// Settings sections for vertical tabs
const SECTIONS = [
  {
    id: 'mode',
    title: 'Interface Mode',
    description: 'Choose your workspace based on your role. Each mode shows different navigation and tools.',
  },
  {
    id: 'appearance',
    title: 'Appearance',
    description: 'Customize the look and feel of the interface to match your preferences.',
  },
  {
    id: 'openclaw',
    title: 'OpenClaw',
    description: 'Connect your AI engine to Telegram and WhatsApp via OpenClaw gateway.',
  },
  {
    id: 'system',
    title: 'System Info',
    description: 'View system capabilities, script permissions, and environment details.',
  },
];

const AUTO_PLAY_DURATION = 8000;

export function Settings() {
  const {
    mode, setMode,
    theme, setTheme,
    serverScriptsEnabled, hasScriptManagerRole,
  } = useUIStore();

  const [activeIndex, setActiveIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [isPaused, setIsPaused] = useState(true); // Start paused for settings

  const handleTabClick = (index: number) => {
    if (index === activeIndex) return;
    setDirection(index > activeIndex ? 1 : -1);
    setActiveIndex(index);
    setIsPaused(true);
  };

  const contentVariants = {
    enter: (dir: number) => ({
      y: dir > 0 ? 24 : -24,
      opacity: 0,
    }),
    center: {
      y: 0,
      opacity: 1,
    },
    exit: (dir: number) => ({
      y: dir > 0 ? -24 : 24,
      opacity: 0,
    }),
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-border/30 bg-gradient-to-br from-primary/5 via-transparent to-violet-500/3 p-6"
      >
        <div className="absolute top-0 right-0 w-48 h-48 bg-primary/5 rounded-full blur-[60px] -translate-y-1/2 translate-x-1/3" />
        <div className="relative">
          <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure your workspace, appearance, and system preferences.
          </p>
        </div>
      </motion.div>

      {/* Capability Badges */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-wrap gap-2"
      >
        <Badge variant={serverScriptsEnabled ? 'default' : 'secondary'} className="gap-1.5">
          {serverScriptsEnabled && <CheckCircle2 className="size-3" />}
          Server Scripts: {serverScriptsEnabled ? 'Enabled' : 'Disabled'}
        </Badge>
        <Badge variant={hasScriptManagerRole ? 'default' : 'secondary'} className="gap-1.5">
          {hasScriptManagerRole && <CheckCircle2 className="size-3" />}
          Script Manager: {hasScriptManagerRole ? 'Yes' : 'No'}
        </Badge>
      </motion.div>

      {!serverScriptsEnabled && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Server-side scripting is disabled. Client Scripts, Workflows, and Custom Fields work normally.
            Add <code className="rounded bg-muted px-1 py-0.5 text-xs">server_script_enabled: 1</code> to
            your site config and restart bench to unlock Server Scripts.
          </AlertDescription>
        </Alert>
      )}

      {/* Vertical Tabs Layout */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start"
      >
        {/* Left: Tab Navigation */}
        <div className="lg:col-span-4 flex flex-col">
          <div className="flex flex-col space-y-0">
            {SECTIONS.map((section, index) => {
              const isActive = activeIndex === index;
              return (
                <button
                  key={section.id}
                  onClick={() => handleTabClick(index)}
                  className={cn(
                    'group relative flex items-start gap-3 py-5 text-left transition-all duration-500 border-t border-border/30 first:border-0',
                    isActive ? 'text-foreground' : 'text-muted-foreground/60 hover:text-foreground'
                  )}
                >
                  {/* Progress bar on left */}
                  <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-muted/50">
                    {isActive && (
                      <motion.div
                        key={`progress-${index}`}
                        className="absolute top-0 left-0 w-full bg-primary origin-top"
                        initial={{ height: '0%' }}
                        animate={isPaused ? {} : { height: '100%' }}
                        transition={{
                          duration: AUTO_PLAY_DURATION / 1000,
                          ease: 'linear',
                        }}
                      />
                    )}
                  </div>

                  <span className="text-[9px] font-medium mt-0.5 tabular-nums opacity-40 ml-3">
                    /{String(index + 1).padStart(2, '0')}
                  </span>

                  <div className="flex flex-col gap-1.5 flex-1">
                    <span className={cn(
                      'text-lg font-medium tracking-tight transition-colors duration-500',
                      isActive ? 'text-foreground' : ''
                    )}>
                      {section.title}
                    </span>

                    <AnimatePresence mode="wait">
                      {isActive && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
                          className="overflow-hidden"
                        >
                          <p className="text-muted-foreground text-xs leading-relaxed max-w-xs">
                            {section.description}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Content Panel */}
        <div className="lg:col-span-8">
          <div className="relative rounded-2xl border border-border/50 bg-card overflow-hidden min-h-[360px]">
            <AnimatePresence initial={false} custom={direction} mode="wait">
              <motion.div
                key={activeIndex}
                custom={direction}
                variants={contentVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{
                  y: { type: 'spring', stiffness: 280, damping: 30 },
                  opacity: { duration: 0.25 },
                }}
                className="p-6"
              >
                {activeIndex === 0 && (
                  <ModePanel mode={mode} onModeChange={setMode} />
                )}
                {activeIndex === 1 && (
                  <AppearancePanel theme={theme} onThemeChange={setTheme} />
                )}
                {activeIndex === 2 && (
                  <OpenClawPanel />
                )}
                {activeIndex === 3 && (
                  <SystemPanel
                    serverScriptsEnabled={serverScriptsEnabled}
                    hasScriptManagerRole={hasScriptManagerRole}
                  />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// --------------- Mode Selection Panel ---------------
function ModePanel({ mode, onModeChange }: { mode: UIMode; onModeChange: (m: UIMode) => void }) {
  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <UserCog className="size-5 text-primary" />
          Interface Mode
        </h3>
        <p className="text-sm text-muted-foreground mt-1">Select the workspace that fits your role.</p>
      </div>

      <div className="space-y-3">
        {modeOptions.map(({ value, label, description, icon: Icon }) => {
          const isSelected = mode === value;
          return (
            <motion.button
              key={value}
              onClick={() => onModeChange(value)}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={cn(
                'w-full flex items-start gap-4 rounded-xl p-4 text-left transition-all duration-200 border',
                isSelected
                  ? 'border-primary/40 bg-primary/5 shadow-sm'
                  : 'border-border/30 hover:border-border hover:bg-muted/30'
              )}
            >
              <div className={cn(
                'flex size-10 items-center justify-center rounded-xl shrink-0 transition-colors',
                isSelected ? 'bg-primary/15' : 'bg-muted'
              )}>
                <Icon className={cn('size-5', isSelected ? 'text-primary' : 'text-muted-foreground')} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-foreground">{label}</p>
                  {isSelected && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                    >
                      <CheckCircle2 className="size-4 text-primary" />
                    </motion.div>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{description}</p>
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

// --------------- Appearance Panel ---------------
function AppearancePanel({ theme, onThemeChange }: { theme: string; onThemeChange: (t: 'light' | 'dark' | 'system') => void }) {
  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Palette className="size-5 text-primary" />
          Appearance
        </h3>
        <p className="text-sm text-muted-foreground mt-1">Choose your preferred color scheme.</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {themeOptions.map(({ value, label, icon: Icon }) => {
          const isSelected = theme === value;
          return (
            <motion.button
              key={value}
              onClick={() => onThemeChange(value)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className={cn(
                'flex flex-col items-center gap-3 rounded-xl p-5 border transition-all duration-200',
                isSelected
                  ? 'border-primary/40 bg-primary/5 shadow-sm'
                  : 'border-border/30 hover:border-border hover:bg-muted/30'
              )}
            >
              <div className={cn(
                'flex size-12 items-center justify-center rounded-xl transition-colors',
                isSelected ? 'bg-primary/15' : 'bg-muted'
              )}>
                <Icon className={cn('size-6', isSelected ? 'text-primary' : 'text-muted-foreground')} />
              </div>
              <span className={cn(
                'text-sm font-medium',
                isSelected ? 'text-foreground' : 'text-muted-foreground'
              )}>
                {label}
              </span>
              {isSelected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                >
                  <CheckCircle2 className="size-4 text-primary" />
                </motion.div>
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

// --------------- OpenClaw Panel ---------------
interface OpenClawStatus {
  success: boolean;
  tool_count: number;
  provider: string;
  model: string;
  telegram_configured: boolean;
  user_mappings: number;
  issues: string[];
}

interface GenerateConfigResult {
  success: boolean;
  config_path: string;
  config: Record<string, unknown>;
  instructions: string[];
}

function OpenClawPanel() {
  const [status, setStatus] = useState<OpenClawStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [configResult, setConfigResult] = useState<GenerateConfigResult | null>(null);
  const [testingMcp, setTestingMcp] = useState(false);
  const [mcpTestResult, setMcpTestResult] = useState<{ success: boolean; tool_count?: number; tools?: string[]; error?: string } | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/method/mcp_ui.api.openclaw.get_openclaw_status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
        },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setStatus(data.message);
    } catch {
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetch('/api/method/mcp_ui.api.openclaw.generate_config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
        },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setConfigResult(data.message);
    } catch {
      setConfigResult(null);
    } finally {
      setGenerating(false);
    }
  };

  const handleTestMcp = async () => {
    setTestingMcp(true);
    try {
      const res = await fetch('/api/method/mcp_ui.api.openclaw.test_mcp_server', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
        },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setMcpTestResult(data.message);
    } catch {
      setMcpTestResult({ success: false, error: 'Network error' });
    } finally {
      setTestingMcp(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Bot className="size-5 text-primary" />
          OpenClaw Gateway
        </h3>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your AI engine to Telegram and WhatsApp. Same tools, same permissions.
        </p>
      </div>

      {/* Status Overview */}
      {status && (
        <div className="grid grid-cols-2 gap-3">
          <div className={cn(
            'rounded-xl border px-4 py-3',
            status.telegram_configured ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-amber-500/20 bg-amber-500/5'
          )}>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Telegram</p>
            <p className={cn('text-sm font-semibold mt-0.5', status.telegram_configured ? 'text-emerald-600' : 'text-amber-600')}>
              {status.telegram_configured ? 'Configured' : 'Not configured'}
            </p>
          </div>
          <div className="rounded-xl border border-border/30 px-4 py-3">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">User Mappings</p>
            <p className="text-sm font-semibold mt-0.5">{status.user_mappings} users</p>
          </div>
          <div className="rounded-xl border border-border/30 px-4 py-3">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">AI Provider</p>
            <p className="text-sm font-semibold mt-0.5">{status.provider}</p>
          </div>
          <div className="rounded-xl border border-border/30 px-4 py-3">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Tools</p>
            <p className="text-sm font-semibold mt-0.5">{status.tool_count} available</p>
          </div>
        </div>
      )}

      {/* Issues */}
      {status?.issues && status.issues.length > 0 && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
          <p className="text-sm font-medium text-amber-700 flex items-center gap-2">
            <AlertCircle className="size-4" />
            Setup Incomplete
          </p>
          <ul className="text-xs text-amber-600 space-y-1 ml-6 list-disc">
            {status.issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
          <p className="text-xs text-muted-foreground mt-2">
            Configure these in{' '}
            <a
              href="/app/mcp-settings"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline inline-flex items-center gap-1"
            >
              MCP Settings <ExternalLink className="size-3" />
            </a>
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-4 py-2.5 text-sm font-medium text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
        >
          {generating ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          {generating ? 'Generating...' : 'Generate Config'}
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleTestMcp}
          disabled={testingMcp}
          className="flex items-center gap-2 rounded-xl border border-border/30 px-4 py-2.5 text-sm font-medium text-foreground hover:bg-muted/30 transition-colors disabled:opacity-50"
        >
          {testingMcp ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          {testingMcp ? 'Testing...' : 'Test MCP Server'}
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={fetchStatus}
          className="flex items-center gap-2 rounded-xl border border-border/30 px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors"
        >
          <RefreshCw className="size-4" />
          Refresh
        </motion.button>
      </div>

      {/* MCP Test Result */}
      {mcpTestResult && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            'rounded-xl border p-4',
            mcpTestResult.success ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5'
          )}
        >
          <p className={cn('text-sm font-medium', mcpTestResult.success ? 'text-emerald-700' : 'text-red-700')}>
            {mcpTestResult.success
              ? `MCP Server OK — ${mcpTestResult.tool_count} tools loaded`
              : `MCP Server Error: ${mcpTestResult.error}`
            }
          </p>
          {mcpTestResult.tools && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {mcpTestResult.tools.map(tool => (
                <span key={tool} className="text-[10px] rounded-md bg-emerald-500/10 px-2 py-0.5 text-emerald-700 font-mono">
                  {tool}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Generated Config */}
      {configResult?.success && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-border/30 bg-muted/20 overflow-hidden"
        >
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/30">
            <p className="text-xs font-medium text-muted-foreground">openclaw.json</p>
            <button
              onClick={() => navigator.clipboard.writeText(JSON.stringify(configResult.config, null, 2))}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <Copy className="size-3" />
              Copy
            </button>
          </div>
          <pre className="p-4 text-xs font-mono text-foreground/80 overflow-x-auto max-h-[240px] overflow-y-auto">
            {JSON.stringify(configResult.config, null, 2)}
          </pre>
          <div className="px-4 py-3 border-t border-border/30 space-y-1">
            {configResult.instructions.map((inst, i) => (
              <p key={i} className="text-xs text-muted-foreground font-mono">{inst}</p>
            ))}
          </div>
        </motion.div>
      )}

      {/* Setup Guide */}
      <div className="rounded-xl border border-border/30 p-4 space-y-3">
        <h4 className="text-sm font-semibold">Quick Setup</h4>
        <ol className="text-xs text-muted-foreground space-y-2 list-decimal ml-4">
          <li>
            Create a Telegram bot via{' '}
            <span className="font-semibold text-foreground">@BotFather</span> and copy the token
          </li>
          <li>
            Go to{' '}
            <a href="/app/mcp-settings" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
              MCP Settings
            </a>{' '}
            — enable OpenClaw and paste the bot token
          </li>
          <li>Add Telegram user mappings (Telegram username → Frappe user)</li>
          <li>Click <span className="font-semibold text-foreground">Generate Config</span> above</li>
          <li>
            Install and run OpenClaw:{' '}
            <code className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono">npm install -g openclaw && openclaw</code>
          </li>
        </ol>
      </div>
    </div>
  );
}


// --------------- System Panel ---------------
function SystemPanel({ serverScriptsEnabled, hasScriptManagerRole }: { serverScriptsEnabled: boolean; hasScriptManagerRole: boolean }) {
  const capabilities = [
    { label: 'Client Scripts', enabled: true, description: 'Form customization, field validation, custom buttons' },
    { label: 'Server Scripts', enabled: serverScriptsEnabled, description: 'Server-side validation, scheduled jobs, custom APIs' },
    { label: 'Script Manager Role', enabled: hasScriptManagerRole, description: 'Permission to create and manage scripts' },
    { label: 'Workflows', enabled: true, description: 'Document approval workflows with state transitions' },
    { label: 'Custom Fields', enabled: true, description: 'Add fields to existing DocTypes without core changes' },
  ];

  return (
    <div className="space-y-4">
      <div className="mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Info className="size-5 text-primary" />
          System Capabilities
        </h3>
        <p className="text-sm text-muted-foreground mt-1">
          Your current environment's available features.
        </p>
      </div>

      <div className="space-y-2">
        {capabilities.map((cap, i) => (
          <motion.div
            key={cap.label}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={cn(
              'flex items-center gap-3 rounded-xl px-4 py-3 border',
              cap.enabled
                ? 'border-emerald-500/20 bg-emerald-500/5'
                : 'border-border/30 bg-muted/20'
            )}
          >
            <div className={cn(
              'flex size-8 items-center justify-center rounded-lg shrink-0',
              cap.enabled ? 'bg-emerald-500/10' : 'bg-muted'
            )}>
              <CheckCircle2 className={cn(
                'size-4',
                cap.enabled ? 'text-emerald-500' : 'text-muted-foreground/40'
              )} />
            </div>
            <div className="flex-1 min-w-0">
              <p className={cn('text-sm font-medium', cap.enabled ? 'text-foreground' : 'text-muted-foreground')}>
                {cap.label}
              </p>
              <p className="text-[11px] text-muted-foreground">{cap.description}</p>
            </div>
            <Badge variant={cap.enabled ? 'default' : 'secondary'} className="text-[10px] shrink-0">
              {cap.enabled ? 'Active' : 'Inactive'}
            </Badge>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
