/**
 * ToolGrid Component
 * Grid display of MCP tools with search and filters
 */
import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ToolCard } from './ToolCard';
import { Search } from 'lucide-react';
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
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-full sm:w-48">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category === 'all' ? 'All Categories' : category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Tool Grid */}
      {filteredTools.length === 0 ? (
        <div className="flex h-64 items-center justify-center rounded-lg border border-dashed">
          <p className="text-sm text-muted-foreground">No tools found</p>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredTools.map((tool) => (
            <ToolCard key={tool.name} tool={tool} onExecute={onExecute} />
          ))}
        </div>
      )}
    </div>
  );
}

