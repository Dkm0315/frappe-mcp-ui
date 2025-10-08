/**
 * ToolCard Component
 * Displays a single MCP tool with metadata
 */
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Coins, AlertTriangle, Lock, Eye } from 'lucide-react';
import { motion } from 'framer-motion';
import type { MCPTool } from '@/types';

interface ToolCardProps {
  tool: MCPTool;
  onExecute: (tool: MCPTool) => void;
}

export function ToolCard({ tool, onExecute }: ToolCardProps) {
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      CRUD: 'bg-blue-500/10 text-blue-700 border-blue-200',
      Query: 'bg-green-500/10 text-green-700 border-green-200',
      Reports: 'bg-purple-500/10 text-purple-700 border-purple-200',
      Bulk: 'bg-orange-500/10 text-orange-700 border-orange-200',
      Export: 'bg-cyan-500/10 text-cyan-700 border-cyan-200',
      Analytics: 'bg-pink-500/10 text-pink-700 border-pink-200',
    };
    return colors[category] || 'bg-gray-500/10 text-gray-700 border-gray-200';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="h-full transition-shadow hover:shadow-lg">
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{tool.title}</CardTitle>
            {tool.destructive && (
              <AlertTriangle className="size-5 text-red-600" title="Destructive operation" />
            )}
            {tool.read_only && (
              <Eye className="size-5 text-blue-600" title="Read-only operation" />
            )}
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            <Badge className={getCategoryColor(tool.category)} variant="outline">
              {tool.category}
            </Badge>
            <Badge variant="secondary" className="gap-1">
              <Coins className="size-3" />
              {tool.base_cost}
            </Badge>
          </div>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-3">{tool.description}</p>
        </CardContent>

        <CardFooter>
          <Button
            className="w-full"
            onClick={() => onExecute(tool)}
            variant={tool.destructive ? 'destructive' : 'default'}
          >
            {tool.destructive && <AlertTriangle className="mr-2 size-4" />}
            {tool.read_only && <Lock className="mr-2 size-4" />}
            Execute Tool
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  );
}

