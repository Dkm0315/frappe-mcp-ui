/**
 * Tools Page
 * Animated tool marketplace with view-switching (list/card/pack) using uselayouts pattern
 */
import { useState } from 'react';
import {
  motion,
  LayoutGroup,
  AnimatePresence,
  type Transition,
} from 'motion/react';
import { cn } from '@/lib/utils';
import { ToolExecutor } from '@/components/tools/ToolExecutor';
import { useMCPTools } from '@/hooks/useMCPTools';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Wrench,
  Coins,
  AlertTriangle,
  Eye,
  ArrowRight,
  Play,
} from 'lucide-react';
import { HugeiconsIcon } from '@hugeicons/react';
import {
  Playlist01Icon,
  GridViewIcon,
  Layers01Icon,
} from '@hugeicons/core-free-icons';
import type { MCPTool } from '@/types';

const snappySpring: Transition = {
  type: 'spring',
  stiffness: 350,
  damping: 30,
  mass: 1,
};

type ViewMode = 'list' | 'card' | 'pack';

const categoryColors: Record<string, { dot: string; bg: string; text: string; border: string }> = {
  CRUD: { dot: 'bg-blue-500', bg: 'bg-blue-500/8', text: 'text-blue-600', border: 'border-blue-500/20' },
  Query: { dot: 'bg-emerald-500', bg: 'bg-emerald-500/8', text: 'text-emerald-600', border: 'border-emerald-500/20' },
  Reports: { dot: 'bg-violet-500', bg: 'bg-violet-500/8', text: 'text-violet-600', border: 'border-violet-500/20' },
  Bulk: { dot: 'bg-amber-500', bg: 'bg-amber-500/8', text: 'text-amber-600', border: 'border-amber-500/20' },
  Export: { dot: 'bg-cyan-500', bg: 'bg-cyan-500/8', text: 'text-cyan-600', border: 'border-cyan-500/20' },
  Analytics: { dot: 'bg-rose-500', bg: 'bg-rose-500/8', text: 'text-rose-600', border: 'border-rose-500/20' },
};

const defaultCategoryColor = { dot: 'bg-gray-500', bg: 'bg-gray-500/8', text: 'text-gray-600', border: 'border-gray-500/20' };

// --------------- Tab Button (animated indicator) ---------------
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
        'relative flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium uppercase tracking-wide transition-all rounded-full outline-none',
        active
          ? 'text-primary-foreground'
          : 'text-muted-foreground hover:text-foreground'
      )}
    >
      {active && (
        <motion.div
          layoutId="tools-view-tab"
          className="absolute inset-0 bg-primary rounded-full shadow-md"
          transition={snappySpring}
        />
      )}
      <span className="relative z-10 flex items-center gap-1.5">
        <HugeiconsIcon icon={icon} size={15} />
        {label}
      </span>
    </button>
  );
}

// --------------- Category Filter Pill ---------------
function CategoryPill({
  category,
  active,
  onClick,
}: {
  category: string;
  active: boolean;
  onClick: () => void;
}) {
  const cfg = categoryColors[category] || defaultCategoryColor;

  return (
    <button
      onClick={onClick}
      className={cn(
        'relative rounded-full px-3 py-1.5 text-[11px] font-medium transition-all',
        active
          ? cn('text-foreground', cfg.bg, cfg.border, 'border')
          : 'text-muted-foreground hover:text-foreground hover:bg-muted/60'
      )}
    >
      {active && category !== 'All' && (
        <span className={cn('inline-block size-1.5 rounded-full mr-1.5', cfg.dot)} />
      )}
      {category}
    </button>
  );
}

// --------------- Main ---------------
export function Tools() {
  const { data: tools, isLoading } = useMCPTools();
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [view, setView] = useState<ViewMode>('card');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');

  const categories = ['All', ...new Set(tools?.map(t => t.category) || [])];

  const filteredTools = (tools || []).filter(tool => {
    const matchesSearch =
      tool.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'All' || tool.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-2xl font-bold tracking-tight"
            >
              Tools
            </motion.h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Browse, search, and execute MCP tools
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="gap-1.5 h-7 text-xs">
              <Wrench className="size-3" />
              {tools?.length || 0} available
            </Badge>
          </div>
        </div>

        {/* Search + View Toggle + Categories */}
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {/* Search */}
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search tools..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-sm rounded-xl border-border/50"
              />
            </div>

            {/* View Toggle */}
            <LayoutGroup>
              <div className="flex p-0.5 bg-muted/80 rounded-full border border-border/50 w-fit">
                <ViewTab active={view === 'list'} onClick={() => setView('list')} icon={Playlist01Icon} label="List" />
                <ViewTab active={view === 'card'} onClick={() => setView('card')} icon={GridViewIcon} label="Cards" />
                <ViewTab active={view === 'pack'} onClick={() => setView('pack')} icon={Layers01Icon} label="Compact" />
              </div>
            </LayoutGroup>
          </div>

          {/* Category Filters */}
          <div className="flex flex-wrap gap-1">
            {categories.map(cat => (
              <CategoryPill
                key={cat}
                category={cat}
                active={categoryFilter === cat}
                onClick={() => setCategoryFilter(cat)}
              />
            ))}
          </div>
        </div>

        {/* Tool Grid */}
        {isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-36 rounded-2xl border border-border/30 bg-muted/30 animate-pulse" />
            ))}
          </div>
        ) : filteredTools.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex h-48 items-center justify-center rounded-2xl border border-dashed border-border/50"
          >
            <div className="text-center space-y-2">
              <Wrench className="size-8 text-muted-foreground/30 mx-auto" />
              <p className="text-sm text-muted-foreground">
                {searchQuery || categoryFilter !== 'All'
                  ? 'No tools match your filters'
                  : 'No tools available'}
              </p>
            </div>
          </motion.div>
        ) : (
          <LayoutGroup>
            <motion.div
              layout
              transition={snappySpring}
              className={cn(
                'w-full',
                view === 'list' && 'flex flex-col gap-0',
                view === 'card' && 'grid gap-3 sm:grid-cols-2 lg:grid-cols-3',
                view === 'pack' && 'grid gap-2 grid-cols-2 sm:grid-cols-3 lg:grid-cols-4'
              )}
            >
              <AnimatePresence mode="popLayout">
                {filteredTools.map((tool, index) => {
                  const cfg = categoryColors[tool.category] || defaultCategoryColor;

                  return (
                    <motion.div
                      key={tool.name}
                      layout
                      initial={{ opacity: 0, scale: 0.97 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.97 }}
                      transition={{ ...snappySpring, delay: Math.min(index * 0.02, 0.3) }}
                    >
                      <motion.button
                        onClick={() => setSelectedTool(tool)}
                        whileHover={{ scale: view === 'list' ? 1 : 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className={cn(
                          'group w-full text-left outline-none transition-all duration-200',

                          // List view
                          view === 'list' &&
                            'flex items-center gap-4 rounded-xl px-4 py-3.5 hover:bg-muted/50 border-b border-border/20 last:border-0',

                          // Card view
                          view === 'card' &&
                            'flex flex-col rounded-2xl border border-border/40 bg-card p-5 hover:shadow-lg hover:shadow-primary/5 hover:border-primary/20',

                          // Pack view
                          view === 'pack' &&
                            'flex flex-col items-center rounded-xl border border-border/30 bg-card p-3 hover:bg-muted/40 hover:border-primary/20'
                        )}
                      >
                        {/* ----- LIST VIEW ----- */}
                        {view === 'list' && (
                          <>
                            <div className={cn('size-2.5 rounded-full shrink-0', cfg.dot)} />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground truncate">
                                {tool.title}
                              </p>
                              <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                                {tool.description}
                              </p>
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                              {tool.destructive && <AlertTriangle className="size-3.5 text-red-500" />}
                              {tool.read_only && !tool.destructive && <Eye className="size-3.5 text-blue-500" />}
                              <Badge variant="outline" className={cn('text-[10px] px-1.5 py-0 h-5', cfg.bg, cfg.text, cfg.border)}>
                                {tool.category}
                              </Badge>
                              <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground tabular-nums">
                                <Coins className="size-2.5" />
                                {tool.base_cost}
                              </span>
                              <ArrowRight className="size-3.5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                            </div>
                          </>
                        )}

                        {/* ----- CARD VIEW ----- */}
                        {view === 'card' && (
                          <>
                            <div className="flex items-start justify-between gap-2 mb-2.5">
                              <h3 className="text-sm font-semibold text-foreground leading-tight">
                                {tool.title}
                              </h3>
                              {tool.destructive && (
                                <div className="flex size-6 items-center justify-center rounded-lg bg-red-500/10 shrink-0">
                                  <AlertTriangle className="size-3.5 text-red-500" />
                                </div>
                              )}
                              {tool.read_only && !tool.destructive && (
                                <div className="flex size-6 items-center justify-center rounded-lg bg-blue-500/10 shrink-0">
                                  <Eye className="size-3.5 text-blue-500" />
                                </div>
                              )}
                            </div>
                            <div className="flex flex-wrap items-center gap-1.5 mb-3">
                              <Badge variant="outline" className={cn('text-[10px] px-1.5 py-0 h-5 font-medium', cfg.bg, cfg.text, cfg.border)}>
                                {tool.category}
                              </Badge>
                              <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
                                <Coins className="size-2.5" />
                                {tool.base_cost}
                              </span>
                            </div>
                            <p className="text-[11px] text-muted-foreground line-clamp-2 mb-4 leading-relaxed">
                              {tool.description}
                            </p>
                            <div className={cn(
                              'mt-auto flex items-center gap-1 text-[11px] font-medium transition-all',
                              tool.destructive ? 'text-red-500' : 'text-primary',
                              'opacity-0 group-hover:opacity-100'
                            )}>
                              <span>Run</span>
                              <Play className="size-3" />
                            </div>
                          </>
                        )}

                        {/* ----- PACK (Compact) VIEW ----- */}
                        {view === 'pack' && (
                          <>
                            <div className={cn('size-2 rounded-full mb-2', cfg.dot)} />
                            <p className="text-[12px] font-medium text-foreground text-center leading-tight">
                              {tool.title.length > 20 ? tool.title.slice(0, 18) + '...' : tool.title}
                            </p>
                            <span className="text-[9px] text-muted-foreground mt-1 uppercase tracking-wider">
                              {tool.category}
                            </span>
                          </>
                        )}
                      </motion.button>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </motion.div>
          </LayoutGroup>
        )}
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
