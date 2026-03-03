/**
 * Dashboard Page
 * Premium, mode-aware home page with animated stats, activity feed, and quick access
 */
import { useState, useEffect } from 'react';
import {
  motion,
  LayoutGroup,
  AnimatePresence,
  type Transition,
} from 'motion/react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/uiStore';
import { useCreditStore } from '@/stores/creditStore';
import { useMCPTools } from '@/hooks/useMCPTools';
import { useSystemStats } from '@/hooks/useDiscovery';
import { useUsageHistory, useCredits } from '@/hooks/useCredits';
import { ToolExecutor } from '@/components/tools/ToolExecutor';
import { Link, useNavigate } from 'react-router-dom';
import {
  Wrench,
  ArrowRight,
  Coins,
  Database,
  Users,
  GitBranch,
  CheckCircle2,
  XCircle,
  Clock,
  Code2,
  MessageSquare,
  Zap,
  Terminal,
  Workflow,
  Bug,
  TrendingUp,
  Activity,
  Layers,
  Play,
} from 'lucide-react';
import { HugeiconsIcon } from '@hugeicons/react';
import {
  Playlist01Icon,
  GridViewIcon,
  Layers01Icon,
} from '@hugeicons/core-free-icons';
import { formatDistanceToNow } from 'date-fns';
import type { MCPTool, UsageLog } from '@/types';

const snappySpring: Transition = {
  type: 'spring',
  stiffness: 350,
  damping: 30,
  mass: 1,
};

const fastFade: Transition = {
  duration: 0.1,
  ease: 'linear',
};

// --------------- Animated Counter ---------------
function AnimatedNumber({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value === 0) { setDisplay(0); return; }
    const duration = 600;
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    const interval = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplay(value);
        clearInterval(interval);
      } else {
        setDisplay(Math.round(current));
      }
    }, duration / steps);
    return () => clearInterval(interval);
  }, [value]);

  return (
    <span className="tabular-nums">{display.toLocaleString()}{suffix}</span>
  );
}

// --------------- Stat Card ---------------
function StatCard({
  icon: Icon,
  label,
  value,
  color,
  href,
  delay = 0,
}: {
  icon: typeof Database;
  label: string;
  value: number;
  color: string;
  href?: string;
  delay?: number;
}) {
  const content = (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ ...snappySpring, delay }}
      whileHover={{ y: -3, scale: 1.02 }}
      className={cn(
        'group relative overflow-hidden rounded-2xl border border-border/50 bg-card p-5',
        'hover:shadow-lg hover:shadow-primary/5 transition-shadow duration-300',
        href && 'cursor-pointer'
      )}
    >
      {/* Gradient glow behind icon */}
      <div className={cn('absolute -top-6 -right-6 size-24 rounded-full blur-2xl opacity-20', color)} />

      <div className="relative flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
            {label}
          </p>
          <p className="text-3xl font-bold text-foreground">
            <AnimatedNumber value={value} />
          </p>
        </div>
        <div className={cn('flex size-10 items-center justify-center rounded-xl', color.replace('bg-', 'bg-').replace('/20', '/10'))}>
          <Icon className={cn('size-5', color.replace('bg-', 'text-').replace('/20', ''))} />
        </div>
      </div>

      {href && (
        <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
          <span>View all</span>
          <ArrowRight className="size-3" />
        </div>
      )}
    </motion.div>
  );

  if (href) return <Link to={href}>{content}</Link>;
  return content;
}

// --------------- View-Switching Tool Grid (uselayouts pattern) ---------------
type ViewMode = 'list' | 'card';

function ViewTab({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: any;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'relative flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium uppercase tracking-wide transition-all rounded-full outline-none',
        active
          ? 'text-primary-foreground'
          : 'text-muted-foreground hover:text-foreground'
      )}
    >
      {active && (
        <motion.div
          layoutId="tool-view-tab"
          className="absolute inset-0 bg-primary rounded-full shadow-sm"
          transition={snappySpring}
        />
      )}
      <span className="relative z-10 flex items-center gap-1.5">
        <HugeiconsIcon icon={icon} size={14} />
        {label}
      </span>
    </button>
  );
}

function ToolShowcase({
  tools,
  onExecute,
}: {
  tools: MCPTool[];
  onExecute: (tool: MCPTool) => void;
}) {
  const [view, setView] = useState<ViewMode>('card');

  const categoryColors: Record<string, string> = {
    CRUD: 'bg-blue-500',
    Query: 'bg-emerald-500',
    Reports: 'bg-violet-500',
    Bulk: 'bg-amber-500',
    Export: 'bg-cyan-500',
    Analytics: 'bg-rose-500',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex size-7 items-center justify-center rounded-lg bg-primary/10">
            <Zap className="size-3.5 text-primary" />
          </div>
          <h2 className="text-sm font-semibold text-foreground">Popular Tools</h2>
        </div>

        <div className="flex items-center gap-3">
          <LayoutGroup>
            <div className="flex p-0.5 bg-muted/80 rounded-full border border-border/50">
              <ViewTab active={view === 'list'} onClick={() => setView('list')} icon={Playlist01Icon} label="List" />
              <ViewTab active={view === 'card'} onClick={() => setView('card')} icon={GridViewIcon} label="Cards" />
            </div>
          </LayoutGroup>

          <Link
            to="/tools"
            className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            All tools
            <ArrowRight className="size-3" />
          </Link>
        </div>
      </div>

      <LayoutGroup>
        <motion.div
          layout
          transition={snappySpring}
          className={cn(
            'w-full',
            view === 'list' && 'flex flex-col gap-1',
            view === 'card' && 'grid grid-cols-2 lg:grid-cols-4 gap-3'
          )}
        >
          {tools.map((tool, index) => {
            const dotColor = categoryColors[tool.category] || 'bg-gray-500';

            return (
              <motion.div
                key={tool.name}
                layout
                transition={snappySpring}
                className="relative"
              >
                <motion.button
                  onClick={() => onExecute(tool)}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className={cn(
                    'group w-full text-left transition-all duration-200 outline-none',
                    view === 'list' &&
                      'flex items-center gap-4 rounded-xl px-4 py-3 hover:bg-muted/60',
                    view === 'card' &&
                      'flex flex-col rounded-2xl border border-border/50 bg-card p-4 hover:shadow-md hover:shadow-primary/5 hover:border-primary/20'
                  )}
                >
                  {view === 'list' ? (
                    <>
                      <div className={cn('size-2 rounded-full shrink-0', dotColor)} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {tool.title}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-wide">
                          {tool.category}
                        </span>
                        <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
                          <Coins className="size-2.5" />
                          {tool.base_cost}
                        </span>
                      </div>
                      <ArrowRight className="size-3.5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                    </>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 mb-2">
                        <div className={cn('size-2 rounded-full', dotColor)} />
                        <span className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-wide">
                          {tool.category}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-foreground mb-1 leading-tight">
                        {tool.title}
                      </h3>
                      <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed mb-3">
                        {tool.description}
                      </p>
                      <div className="mt-auto flex items-center justify-between">
                        <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
                          <Coins className="size-2.5" />
                          {tool.base_cost} credits
                        </span>
                        <span className="flex items-center gap-1 text-[11px] font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                          Run <Play className="size-3" />
                        </span>
                      </div>
                    </>
                  )}
                </motion.button>

                {view === 'list' && index < tools.length - 1 && (
                  <div className="ml-10 h-px bg-border/30" />
                )}
              </motion.div>
            );
          })}
        </motion.div>
      </LayoutGroup>
    </div>
  );
}

// --------------- Activity Feed Item ---------------
function ActivityItem({ log, index }: { log: UsageLog; index: number }) {
  const statusConfig = {
    Success: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    Failed: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
    Partial: { icon: Clock, color: 'text-amber-500', bg: 'bg-amber-500/10' },
  };

  const cfg = statusConfig[log.status] || statusConfig.Partial;
  const StatusIcon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className="flex items-center gap-3 rounded-xl px-3 py-2.5 hover:bg-muted/40 transition-colors"
    >
      <div className={cn('flex size-8 items-center justify-center rounded-lg shrink-0', cfg.bg)}>
        <StatusIcon className={cn('size-3.5', cfg.color)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-medium text-foreground truncate">{log.tool_name}</p>
        <p className="text-[11px] text-muted-foreground">
          {formatDistanceToNow(new Date(log.creation), { addSuffix: true })}
        </p>
      </div>
      <span className="text-[11px] font-mono font-medium text-muted-foreground shrink-0">
        -{log.credits_consumed}
      </span>
    </motion.div>
  );
}

// --------------- Quick Action Card for Dev/Assistant ---------------
function QuickActionCard({
  icon: Icon,
  title,
  description,
  href,
  color,
  delay = 0,
}: {
  icon: typeof Code2;
  title: string;
  description: string;
  href: string;
  color: string;
  delay?: number;
}) {
  return (
    <Link to={href}>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...snappySpring, delay }}
        whileHover={{ y: -4, scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="group relative overflow-hidden rounded-2xl border border-border/50 bg-card p-5 cursor-pointer hover:shadow-lg hover:shadow-primary/5 transition-shadow"
      >
        <div className={cn('absolute -top-8 -right-8 size-28 rounded-full blur-2xl opacity-10', color)} />

        <div className="relative">
          <div className={cn('flex size-10 items-center justify-center rounded-xl mb-3', color.replace('bg-', 'bg-').replace('/20', '/10'))}>
            <Icon className={cn('size-5', color.replace('bg-', 'text-').replace('/20', ''))} />
          </div>
          <h3 className="text-sm font-semibold text-foreground mb-1">{title}</h3>
          <p className="text-[11px] text-muted-foreground leading-relaxed">{description}</p>

          <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
            Open <ArrowRight className="size-3" />
          </div>
        </div>
      </motion.div>
    </Link>
  );
}

// --------------- Main Dashboard ---------------
export function Dashboard() {
  const { mode } = useUIStore();
  const { balance } = useCreditStore();
  const { data: tools, isLoading: toolsLoading } = useMCPTools();
  const { data: stats } = useSystemStats();
  useCredits(); // trigger credit fetch
  const { data: logs } = useUsageHistory(8);
  const navigate = useNavigate();
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);

  const popularTools = tools?.slice(0, 8) || [];
  const recentLogs = logs?.slice(0, 6) || [];

  // Redirect assistant mode to chat
  if (mode === 'assistant') {
    return <AssistantDashboard />;
  }

  if (mode === 'developer') {
    return <DeveloperDashboard />;
  }

  // ----- Admin Dashboard -----
  return (
    <>
      <div className="space-y-8">
        {/* Hero with gradient mesh */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="relative overflow-hidden rounded-2xl border border-border/30 bg-gradient-to-br from-primary/8 via-transparent to-violet-500/5 p-7"
        >
          <div className="absolute top-0 right-0 w-80 h-80 bg-primary/8 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/3" />
          <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-violet-500/8 rounded-full blur-[60px] translate-y-1/2" />

          <div className="relative flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Control Panel
              </h1>
              <p className="mt-1 text-sm text-muted-foreground max-w-md">
                Monitor your system, execute tools, and manage configurations.
              </p>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="hidden sm:flex items-center gap-3 rounded-2xl border border-border/30 bg-card/80 backdrop-blur-sm px-5 py-3"
            >
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
                <Coins className="size-5 text-primary" />
              </div>
              <div>
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">Credits</p>
                <p className="text-xl font-bold tabular-nums text-foreground">
                  <AnimatedNumber value={balance} />
                </p>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Wrench}
            label="Tools"
            value={tools?.length || 0}
            color="bg-blue-500/20"
            href="/tools"
            delay={0.05}
          />
          <StatCard
            icon={Database}
            label="DocTypes"
            value={stats?.total_doctypes || 0}
            color="bg-emerald-500/20"
            delay={0.1}
          />
          <StatCard
            icon={Users}
            label="Users"
            value={stats?.total_users || 0}
            color="bg-violet-500/20"
            delay={0.15}
          />
          <StatCard
            icon={GitBranch}
            label="Workflows"
            value={stats?.active_workflows || 0}
            color="bg-amber-500/20"
            href="/workflows"
            delay={0.2}
          />
        </div>

        {/* Two-column: Tools + Activity */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Tools Showcase (2/3) */}
          <div className="lg:col-span-2">
            {toolsLoading ? (
              <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="h-32 rounded-2xl border border-border/30 bg-muted/30 animate-pulse"
                  />
                ))}
              </div>
            ) : popularTools.length > 0 ? (
              <ToolShowcase tools={popularTools} onExecute={setSelectedTool} />
            ) : (
              <div className="flex h-48 items-center justify-center rounded-2xl border border-dashed border-border/50">
                <p className="text-sm text-muted-foreground">No tools available</p>
              </div>
            )}
          </div>

          {/* Activity Feed (1/3) */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-2xl border border-border/50 bg-card"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-border/30">
              <div className="flex items-center gap-2">
                <Activity className="size-3.5 text-muted-foreground" />
                <h3 className="text-sm font-semibold text-foreground">Recent Activity</h3>
              </div>
              <Link
                to="/history"
                className="text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                View all
              </Link>
            </div>

            <div className="p-2">
              {recentLogs.length === 0 ? (
                <div className="flex h-40 items-center justify-center">
                  <p className="text-[11px] text-muted-foreground">No recent activity</p>
                </div>
              ) : (
                <div className="space-y-0.5">
                  {recentLogs.map((log, i) => (
                    <ActivityItem key={log.name} log={log} index={i} />
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>

      {selectedTool && (
        <ToolExecutor
          tool={selectedTool}
          open={!!selectedTool}
          onClose={() => setSelectedTool(null)}
        />
      )}
    </>
  );
}

// --------------- Developer Dashboard ---------------
function DeveloperDashboard() {
  const { data: stats } = useSystemStats();

  return (
    <div className="space-y-8">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-border/30 bg-gradient-to-br from-indigo-500/8 via-transparent to-cyan-500/5 p-7"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px] -translate-y-1/3 translate-x-1/4" />
        <div className="relative">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Developer IDE</h1>
          <p className="mt-1 text-sm text-muted-foreground max-w-md">
            Write scripts, build workflows, explore APIs, and debug your Frappe system.
          </p>
        </div>
      </motion.div>

      {/* Quick Stats */}
      <div className="grid gap-3 grid-cols-3">
        <StatCard icon={Database} label="DocTypes" value={stats?.total_doctypes || 0} color="bg-emerald-500/20" delay={0.05} />
        <StatCard icon={Layers} label="Custom Fields" value={stats?.total_custom_fields || 0} color="bg-cyan-500/20" delay={0.1} />
        <StatCard icon={GitBranch} label="Workflows" value={stats?.active_workflows || 0} color="bg-violet-500/20" href="/workflow-builder" delay={0.15} />
      </div>

      {/* Quick Actions Grid */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <div className="flex size-7 items-center justify-center rounded-lg bg-indigo-500/10">
            <Zap className="size-3.5 text-indigo-500" />
          </div>
          <h2 className="text-sm font-semibold text-foreground">Quick Actions</h2>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <QuickActionCard
            icon={Code2}
            title="Script Studio"
            description="Create client scripts, server scripts, and custom APIs with Monaco editor"
            href="/scripts"
            color="bg-blue-500/20"
            delay={0.05}
          />
          <QuickActionCard
            icon={Workflow}
            title="Workflow Builder"
            description="Visual drag-and-drop workflow designer with React Flow"
            href="/workflow-builder"
            color="bg-violet-500/20"
            delay={0.1}
          />
          <QuickActionCard
            icon={Database}
            title="Schema Manager"
            description="Browse DocTypes, add custom fields, manage schema changes"
            href="/schema"
            color="bg-emerald-500/20"
            delay={0.15}
          />
          <QuickActionCard
            icon={Terminal}
            title="API Explorer"
            description="Test Frappe REST API endpoints with live request/response"
            href="/api-explorer"
            color="bg-amber-500/20"
            delay={0.2}
          />
          <QuickActionCard
            icon={Bug}
            title="Debug Console"
            description="Real-time error logs, scheduled job status, and background tasks"
            href="/debug"
            color="bg-red-500/20"
            delay={0.25}
          />
          <QuickActionCard
            icon={Wrench}
            title="MCP Tools"
            description="Execute MCP tools directly — CRUD, queries, reports, and bulk operations"
            href="/tools"
            color="bg-cyan-500/20"
            delay={0.3}
          />
        </div>
      </div>
    </div>
  );
}

// --------------- Assistant Dashboard (redirect to chat) ---------------
function AssistantDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate('/chat', { replace: true });
  }, [navigate]);

  return null;
}
