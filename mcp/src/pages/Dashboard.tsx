/**
 * Dashboard Page
 * Home page with credit balance, recent executions, and popular tools
 */
import { useState } from 'react';
import { CreditBalance } from '@/components/credits/CreditBalance';
import { CreditHistory } from '@/components/credits/CreditHistory';
import { ToolCard } from '@/components/tools/ToolCard';
import { PurchaseModal } from '@/components/credits/PurchaseModal';
import { NaturalLanguageInput } from '@/components/modes/NaturalLanguageInput';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useMCPTools } from '@/hooks/useMCPTools';
import { useExecuteTool } from '@/hooks/useExecuteTool';
import { useUIStore } from '@/stores/uiStore';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ToolExecutor } from '@/components/tools/ToolExecutor';
import { toast } from 'sonner';
import type { MCPTool } from '@/types';

export function Dashboard() {
  const { mode } = useUIStore();
  const { data: tools, isLoading } = useMCPTools();
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [toolParams, setToolParams] = useState<Record<string, any>>({});
  const executeMutation = useExecuteTool();

  const popularTools = tools?.slice(0, 4) || [];

  const handleNLPToolSelect = (toolName: string, params: Record<string, any>, nextStep: string) => {
    const tool = tools?.find(t => t.name === toolName);
    if (tool) {
      setToolParams(params);
      setSelectedTool(tool);
    }
  };

  const handleAutoExecute = (toolName: string, params: Record<string, any>) => {
    const tool = tools?.find(t => t.name === toolName);
    if (!tool) return;

    toast.loading('Executing...', { id: 'auto-execute' });

    executeMutation.mutate(
      { toolName, params },
      {
        onSuccess: (data) => {
          toast.success(
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span>Executed successfully!</span>
            </div>,
            { id: 'auto-execute', duration: 3000 }
          );
          
          // Show result in modal
          setToolParams(params);
          setSelectedTool(tool);
        },
        onError: (error: any) => {
          toast.error(`Error: ${error.message}`, { id: 'auto-execute' });
        },
      }
    );
  };

  return (
    <>
      <div className="space-y-6">
        {/* Hero Section */}
        <div className="rounded-lg border bg-gradient-to-r from-primary/10 via-primary/5 to-transparent p-6 md:p-8">
          <h1 className="text-3xl font-bold md:text-4xl">
            Welcome to MCP Tools
          </h1>
          <p className="mt-2 text-muted-foreground md:text-lg">
            {mode === 'simple' 
              ? 'Just describe what you want to do in plain English below.' 
              : 'Execute powerful tools with ease. Explore tools in the Tools page.'}
          </p>
        </div>

        {/* Simple Mode: Natural Language Input */}
        {mode === 'simple' && (
          <NaturalLanguageInput 
            onToolSelect={handleNLPToolSelect}
            onAutoExecute={handleAutoExecute}
          />
        )}

        {/* 3-Column Grid */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Credit Balance */}
          <div className="md:col-span-1">
            <CreditBalance />
            <PurchaseModal trigger={
              <Button className="mt-4 w-full">
                Purchase More Credits
              </Button>
            } />
          </div>

          {/* Recent Executions */}
          <div className="md:col-span-2">
            <CreditHistory />
          </div>
        </div>

        {/* Popular Tools */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="size-5" />
              Popular Tools
            </CardTitle>
            <Link to="/tools">
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-48" />
                ))}
              </div>
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {popularTools.map((tool) => (
                  <ToolCard
                    key={tool.name}
                    tool={tool}
                    onExecute={setSelectedTool}
                  />
                ))}
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
          onClose={() => {
            setSelectedTool(null);
            setToolParams({});
          }}
          initialParams={toolParams}
        />
      )}
    </>
  );
}

