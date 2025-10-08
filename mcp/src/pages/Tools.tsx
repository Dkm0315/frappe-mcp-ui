/**
 * Tools Page
 * Tool marketplace with all available tools
 */
import { useState } from 'react';
import { ToolGrid } from '@/components/tools/ToolGrid';
import { ToolExecutor } from '@/components/tools/ToolExecutor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMCPTools } from '@/hooks/useMCPTools';
import { Skeleton } from '@/components/ui/skeleton';
import { Wrench } from 'lucide-react';
import type { MCPTool } from '@/types';

export function Tools() {
  const { data: tools, isLoading } = useMCPTools();
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);

  return (
    <>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">MCP Tools</h1>
          <p className="mt-2 text-muted-foreground">
            Browse and execute available MCP tools
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wrench className="size-5" />
              Available Tools ({tools?.length || 0})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {[...Array(6)].map((_, i) => (
                  <Skeleton key={i} className="h-64" />
                ))}
              </div>
            ) : tools && tools.length > 0 ? (
              <ToolGrid tools={tools} onExecute={setSelectedTool} />
            ) : (
              <div className="flex h-64 items-center justify-center">
                <p className="text-muted-foreground">No tools available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tool Executor Modal */}
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

