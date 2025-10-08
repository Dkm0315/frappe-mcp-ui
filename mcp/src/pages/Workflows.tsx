/**
 * Workflows Page
 * Shows available NextAI Funnel workflows with dynamic categories
 * Includes embedded workflow builder
 */
import { useState, useEffect } from 'react';
import { useUIStore } from '@/stores/uiStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Info, GitBranch, Play, Clock, Edit, Plus, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export function Workflows() {
  const { hasNextAI } = useUIStore();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [workflows, setWorkflows] = useState<any>({});
  const [categories, setCategories] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [builderOpen, setBuilderOpen] = useState(false);
  const [builderUrl, setBuilderUrl] = useState('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
  
  const fetchWorkflows = async () => {
    if (!hasNextAI) return;
    
    setIsLoading(true);
    try {
      const result = await api.getFunnelWorkflows();
      if (result.success) {
        setWorkflows(result.workflows || {});
        setCategories(result.categories || []);
        setTotal(result.total || 0);
      }
    } catch (error: any) {
      toast.error('Failed to load workflows');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Fetch workflows on mount - but only if hasNextAI
  useEffect(() => {
    fetchWorkflows();
  }, [hasNextAI]);
  
  const handleCreateWorkflow = async () => {
    try {
      const result = await api.call('mcp_ui.api.workflow_integration.get_builder_url');
      if (result.success && result.builder_url) {
        setBuilderUrl(result.builder_url);
        setBuilderOpen(true);
      }
    } catch (error: any) {
      toast.error('Failed to open builder');
    }
  };
  
  const handleEditWorkflow = async (workflow: any) => {
    try {
      const result = await api.call('mcp_ui.api.workflow_integration.get_builder_url', {
        funnel_name: workflow.funnel
      });
      if (result.success && result.builder_url) {
        setSelectedWorkflow(workflow);
        setBuilderUrl(result.builder_url);
        setBuilderOpen(true);
      }
    } catch (error: any) {
      toast.error('Failed to open builder');
    }
  };

  // Render "NextAI Required" message if not installed
  if (!hasNextAI) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Workflow Automation</h1>
          <p className="text-muted-foreground mt-2">
            Automate complex multi-step business processes
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              NextAI Required for Advanced Workflows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Install the <strong>NextAI</strong> app to unlock the visual workflow builder with 85+ node types.
                Workflows enable you to automate multi-step processes like MRP execution,
                sales order processing, payroll runs, and more.
              </AlertDescription>
            </Alert>
            
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">Manufacturing</h3>
                <p className="text-sm text-muted-foreground">
                  Automate MRP, work orders, material requests
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">Sales & Finance</h3>
                <p className="text-sm text-muted-foreground">
                  Sales order to invoice, payment collection
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">HR & Payroll</h3>
                <p className="text-sm text-muted-foreground">
                  Salary processing, attendance, leave management
                </p>
              </div>
            </div>
            
            <div className="mt-6">
              <h4 className="font-semibold mb-2">Alternative: Simple Tool Chains</h4>
              <p className="text-sm text-muted-foreground mb-4">
                Without NextAI, you can still create simple automation chains by sequencing MCP tools.
              </p>
              <Button variant="outline" disabled>
                <Plus className="mr-2 h-4 w-4" />
                Create Simple Chain (Coming Soon)
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <GitBranch className="h-8 w-8 text-primary" />
              Workflow Automation
            </h1>
            <p className="text-muted-foreground mt-2">
              Automate complex multi-step business processes with visual workflows
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="text-lg px-4 py-2">
              {total} workflows
            </Badge>
            <Button onClick={handleCreateWorkflow}>
              <Plus className="mr-2 h-4 w-4" />
              Create Workflow
            </Button>
          </div>
        </div>

        {/* Dynamic Category Tabs */}
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
          <TabsList className="flex flex-wrap gap-2">
            <TabsTrigger value="all">All ({total})</TabsTrigger>
            {categories.map(cat => (
              <TabsTrigger key={cat} value={cat} className="capitalize">
                {cat.replace(/_/g, ' ')} ({workflows[cat]?.length || 0})
              </TabsTrigger>
            ))}
          </TabsList>

          {isLoading ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mt-6">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-48" />
              ))}
            </div>
          ) : (
            <>
              <TabsContent value="all" className="mt-6">
                {total === 0 ? (
                  <Card>
                    <CardContent className="p-12 text-center">
                      <GitBranch className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <h3 className="font-semibold mb-2">No Workflows Yet</h3>
                      <p className="text-muted-foreground mb-4">
                        Create your first workflow to automate complex processes
                      </p>
                      <Button onClick={handleCreateWorkflow}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create First Workflow
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {Object.values(workflows).flat().map((wf: any) => (
                      <WorkflowCard 
                        key={wf.name} 
                        workflow={wf} 
                        onEdit={handleEditWorkflow}
                      />
                    ))}
                  </div>
                )}
              </TabsContent>

              {/* Dynamic category tabs */}
              {categories.map(cat => (
                <TabsContent key={cat} value={cat} className="mt-6">
                  <WorkflowGrid 
                    workflows={workflows[cat] || []} 
                    onEdit={handleEditWorkflow}
                  />
                </TabsContent>
              ))}
            </>
          )}
        </Tabs>
      </div>

      {/* Workflow Builder Modal */}
      <Dialog open={builderOpen} onOpenChange={setBuilderOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] p-0">
          <DialogHeader className="p-6 pb-0">
            <DialogTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                {selectedWorkflow ? `Edit: ${selectedWorkflow.funnel}` : 'Create Workflow'}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(builderUrl, '_blank')}
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                Open in New Tab
              </Button>
            </DialogTitle>
          </DialogHeader>
          <div className="h-[80vh]">
            {builderUrl && (
              <iframe
                src={builderUrl}
                className="w-full h-full border-0"
                title="Workflow Builder"
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

interface WorkflowGridProps {
  workflows: any[];
  onEdit: (workflow: any) => void;
}

function WorkflowGrid({ workflows, onEdit }: WorkflowGridProps) {
  if (workflows.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <Info className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            No workflows in this category.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {workflows.map((workflow) => (
        <WorkflowCard key={workflow.name} workflow={workflow} onEdit={onEdit} />
      ))}
    </div>
  );
}

interface WorkflowCardProps {
  workflow: any;
  onEdit: (workflow: any) => void;
}

function WorkflowCard({ workflow, onEdit }: WorkflowCardProps) {
  const [isTriggering, setIsTriggering] = useState(false);
  
  const handleTrigger = async () => {
    setIsTriggering(true);
    try {
      const result = await api.triggerWorkflow(workflow.funnel, {});
      if (result.success) {
        toast.success(`Workflow triggered! ID: ${result.workflow_id}`);
      } else {
        toast.error(result.message || 'Failed to trigger workflow');
      }
    } catch (error: any) {
      toast.error('Failed to trigger workflow');
    } finally {
      setIsTriggering(false);
    }
  };
  
  return (
    <Card className="hover:border-primary transition-colors">
      <CardHeader>
        <CardTitle className="flex items-start justify-between">
          <span className="line-clamp-2">{workflow.funnel}</span>
          <GitBranch className="h-5 w-5 text-muted-foreground flex-shrink-0 ml-2" />
        </CardTitle>
        <CardDescription className="line-clamp-2">
          {workflow.funnel_description || 'No description'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Clock className="h-4 w-4" />
          <span>Modified {new Date(workflow.modified).toLocaleDateString()}</span>
        </div>
        
        <div className="flex gap-2">
          <Button 
            className="flex-1" 
            size="sm"
            onClick={handleTrigger}
            disabled={isTriggering}
          >
            <Play className="h-4 w-4 mr-2" />
            {isTriggering ? 'Triggering...' : 'Trigger'}
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => onEdit(workflow)}
          >
            <Edit className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

