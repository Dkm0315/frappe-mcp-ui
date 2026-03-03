/**
 * ToolCard Component
 * Professional card for displaying MCP tools with category theming
 */
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Coins, AlertTriangle, Eye, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import type { MCPTool } from '@/types';

interface ToolCardProps {
  tool: MCPTool;
  onExecute: (tool: MCPTool) => void;
}

const categoryConfig: Record<string, { bg: string; text: string; border: string; accent: string }> = {
  CRUD: { bg: 'bg-blue-500/8', text: 'text-blue-600', border: 'border-blue-500/20', accent: 'group-hover:border-blue-500/40' },
  Query: { bg: 'bg-emerald-500/8', text: 'text-emerald-600', border: 'border-emerald-500/20', accent: 'group-hover:border-emerald-500/40' },
  Reports: { bg: 'bg-violet-500/8', text: 'text-violet-600', border: 'border-violet-500/20', accent: 'group-hover:border-violet-500/40' },
  Bulk: { bg: 'bg-amber-500/8', text: 'text-amber-600', border: 'border-amber-500/20', accent: 'group-hover:border-amber-500/40' },
  Export: { bg: 'bg-cyan-500/8', text: 'text-cyan-600', border: 'border-cyan-500/20', accent: 'group-hover:border-cyan-500/40' },
  Analytics: { bg: 'bg-rose-500/8', text: 'text-rose-600', border: 'border-rose-500/20', accent: 'group-hover:border-rose-500/40' },
};

const defaultCfg = { bg: 'bg-gray-500/8', text: 'text-gray-600', border: 'border-gray-500/20', accent: 'group-hover:border-gray-500/40' };

export function ToolCard({ tool, onExecute }: ToolCardProps) {
  const cfg = categoryConfig[tool.category] || defaultCfg;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15 }}
    >
      <button
        type="button"
        onClick={() => onExecute(tool)}
        className={cn(
          'group relative flex w-full flex-col rounded-xl border bg-card p-4 text-left transition-all duration-200',
          'hover:shadow-md hover:shadow-primary/5',
          cfg.accent
        )}
      >
        {/* Top row: title + icon */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="text-sm font-semibold text-card-foreground leading-tight">{tool.title}</h3>
          <div className="shrink-0">
            {tool.destructive && (
              <div className="flex size-6 items-center justify-center rounded-md bg-red-500/10">
                <AlertTriangle className="size-3.5 text-red-500" />
              </div>
            )}
            {tool.read_only && !tool.destructive && (
              <div className="flex size-6 items-center justify-center rounded-md bg-blue-500/10">
                <Eye className="size-3.5 text-blue-500" />
              </div>
            )}
          </div>
        </div>

        {/* Category + cost badges */}
        <div className="flex flex-wrap items-center gap-1.5 mb-3">
          <Badge variant="outline" className={cn('text-[10px] px-1.5 py-0 h-5 font-medium', cfg.bg, cfg.text, cfg.border)}>
            {tool.category}
          </Badge>
          <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
            <Coins className="size-3" />
            {tool.base_cost}
          </span>
        </div>

        {/* Description */}
        <p className="text-xs text-muted-foreground line-clamp-2 mb-4 leading-relaxed">{tool.description}</p>

        {/* Bottom: run action */}
        <div className={cn(
          'mt-auto flex items-center gap-1 text-xs font-medium transition-colors',
          tool.destructive ? 'text-red-500' : 'text-primary',
          'opacity-0 group-hover:opacity-100'
        )}>
          <span>Run</span>
          <ArrowRight className="size-3" />
        </div>
      </button>
    </motion.div>
  );
}
