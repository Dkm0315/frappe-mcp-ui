/**
 * ToolGrid Component
 * Grid display of MCP tools with search and filters
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { ToolCard } from './ToolCard';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MCPTool } from '@/types';

interface ToolGridProps {
  tools: MCPTool[];
  onExecute: (tool: MCPTool) => void;
}

export function ToolGrid({ tools, onExecute }: ToolGridProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      tool.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = categoryFilter === 'all' || tool.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  const categories = ['all', ...new Set(tools.map((t) => t.category))];

  return (
    <div className="space-y-5">
      {/* Search and Category Tabs */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-8 text-sm"
          />
        </div>
        <div className="flex flex-wrap gap-1">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setCategoryFilter(category)}
              className={cn(
                'rounded-lg px-2.5 py-1 text-xs font-medium transition-colors',
                categoryFilter === category
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              )}
            >
              {category === 'all' ? 'All' : category}
            </button>
          ))}
        </div>
      </div>

      {/* Tool Grid */}
      {filteredTools.length === 0 ? (
        <div className="flex h-48 items-center justify-center rounded-xl border border-dashed">
          <p className="text-sm text-muted-foreground">No tools found</p>
        </div>
      ) : (
        <motion.div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.04 } },
          }}
        >
          <AnimatePresence mode="popLayout">
            {filteredTools.map((tool) => (
              <motion.div
                key={tool.name}
                layout
                variants={{
                  hidden: { opacity: 0, scale: 0.97 },
                  visible: { opacity: 1, scale: 1 },
                }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ duration: 0.15 }}
              >
                <ToolCard tool={tool} onExecute={onExecute} />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
}
