/**
 * Workflow Builder — n8n-style visual node editor
 * Uses React Flow (@xyflow/react) for a real drag-and-drop canvas.
 * Nodes = workflow states, Edges = transitions with action labels.
 */
import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
  type Node,
  type Edge,
  type Connection,
  type NodeProps,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import {
  Workflow, Plus, Save, Trash2, ArrowLeft, X,
  CircleDot, ArrowRight, Play, Pause, Settings2,
  Zap, GitBranch, ChevronRight,
} from 'lucide-react';

// ── Types ────────────────────────────────────────────────────────────
interface WorkflowState {
  state: string;
  doc_status: string;
  is_optional_state: number;
  allow_edit: string;
}

interface WorkflowTransition {
  state: string;
  action: string;
  next_state: string;
  allowed: string;
  condition: string;
}

interface FrappeWorkflow {
  name: string;
  document_type: string;
  is_active: number;
  modified: string;
  states: WorkflowState[];
  transitions: WorkflowTransition[];
}

// ── Custom Node ──────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, { bg: string; border: string; dot: string }> = {
  '0': { bg: 'bg-amber-500/10', border: 'border-amber-500/30', dot: 'bg-amber-500' },
  '1': { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', dot: 'bg-emerald-500' },
  '2': { bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-500' },
};

const STATUS_LABELS: Record<string, string> = {
  '0': 'Draft',
  '1': 'Submitted',
  '2': 'Cancelled',
};

function StateNode({ data, selected }: NodeProps) {
  const colors = STATUS_COLORS[data.doc_status as string] || STATUS_COLORS['0'];

  return (
    <div className={cn(
      'relative rounded-xl border-2 bg-background shadow-lg px-5 py-4 min-w-[180px] transition-all',
      selected ? 'border-primary shadow-primary/20 ring-2 ring-primary/10' : colors.border,
    )}>
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-primary !border-2 !border-background !-left-1.5"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-primary !border-2 !border-background !-right-1.5"
      />

      <div className="flex items-center gap-2 mb-2">
        <div className={cn('size-2.5 rounded-full', colors.dot)} />
        <span className="text-sm font-semibold truncate">{data.label as string}</span>
      </div>

      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="text-[9px] h-4 px-1.5">
          {STATUS_LABELS[data.doc_status as string] || 'Draft'}
        </Badge>
        {data.allow_edit && (
          <span className="text-[10px] text-muted-foreground truncate">
            Edit: {data.allow_edit as string}
          </span>
        )}
      </div>
    </div>
  );
}

const nodeTypes = { stateNode: StateNode };

// ── Helpers ──────────────────────────────────────────────────────────
function buildNodesAndEdges(
  states: WorkflowState[],
  transitions: WorkflowTransition[],
): { nodes: Node[]; edges: Edge[] } {
  // Auto-layout: arrange nodes in rows
  const nodes: Node[] = states.map((s, i) => ({
    id: s.state,
    type: 'stateNode',
    position: { x: 280 * i + 50, y: 100 + (i % 2) * 100 },
    data: {
      label: s.state,
      doc_status: s.doc_status,
      allow_edit: s.allow_edit,
      is_optional: s.is_optional_state,
    },
  }));

  const edges: Edge[] = transitions.map((t, i) => ({
    id: `e-${i}-${t.state}-${t.next_state}`,
    source: t.state,
    target: t.next_state,
    label: t.action,
    animated: true,
    style: { stroke: 'hsl(var(--primary))', strokeWidth: 2 },
    labelStyle: { fontSize: 11, fontWeight: 600, fill: 'hsl(var(--primary))' },
    labelBgStyle: { fill: 'hsl(var(--background))', strokeWidth: 0 },
    labelBgPadding: [6, 4] as [number, number],
    labelBgBorderRadius: 6,
    markerEnd: { type: MarkerType.ArrowClosed, color: 'hsl(var(--primary))' },
  }));

  return { nodes, edges };
}

function extractWorkflowData(
  nodes: Node[],
  edges: Edge[],
): { states: WorkflowState[]; transitions: WorkflowTransition[] } {
  const states: WorkflowState[] = nodes.map(n => ({
    state: n.id,
    doc_status: (n.data.doc_status as string) || '0',
    is_optional_state: (n.data.is_optional as number) || 0,
    allow_edit: (n.data.allow_edit as string) || 'All',
  }));

  const transitions: WorkflowTransition[] = edges.map(e => ({
    state: e.source,
    action: (e.label as string) || '',
    next_state: e.target,
    allowed: 'All',
    condition: '',
  }));

  return { states, transitions };
}

// ── Properties Panel ─────────────────────────────────────────────────
function PropertiesPanel({
  selectedNode,
  selectedEdge,
  onUpdateNode,
  onUpdateEdge,
  onDeleteNode,
  onDeleteEdge,
  onClose,
}: {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onUpdateNode: (id: string, data: Record<string, any>) => void;
  onUpdateEdge: (id: string, updates: Partial<Edge>) => void;
  onDeleteNode: (id: string) => void;
  onDeleteEdge: (id: string) => void;
  onClose: () => void;
}) {
  if (!selectedNode && !selectedEdge) return null;

  return (
    <div className="absolute top-4 right-4 z-10 w-72 rounded-xl border bg-background/95 backdrop-blur-md shadow-xl">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Settings2 className="size-4 text-primary" />
          <span className="text-sm font-semibold">
            {selectedNode ? 'State Properties' : 'Transition Properties'}
          </span>
        </div>
        <button onClick={onClose} className="rounded-md p-1 hover:bg-muted transition-colors">
          <X className="size-3.5" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {selectedNode && (
          <>
            <div className="space-y-1.5">
              <Label className="text-xs">State Name</Label>
              <Input
                value={selectedNode.data.label as string}
                onChange={(e) => onUpdateNode(selectedNode.id, {
                  ...selectedNode.data,
                  label: e.target.value,
                })}
                className="h-8 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Doc Status</Label>
              <select
                value={selectedNode.data.doc_status as string}
                onChange={(e) => onUpdateNode(selectedNode.id, {
                  ...selectedNode.data,
                  doc_status: e.target.value,
                })}
                className="flex h-8 w-full rounded-md border border-input bg-background px-2 text-sm"
              >
                <option value="0">Draft (0)</option>
                <option value="1">Submitted (1)</option>
                <option value="2">Cancelled (2)</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Allow Edit (Role)</Label>
              <Input
                value={(selectedNode.data.allow_edit as string) || ''}
                onChange={(e) => onUpdateNode(selectedNode.id, {
                  ...selectedNode.data,
                  allow_edit: e.target.value,
                })}
                placeholder="All"
                className="h-8 text-sm"
              />
            </div>
            <Button
              variant="destructive"
              size="sm"
              className="w-full"
              onClick={() => onDeleteNode(selectedNode.id)}
            >
              <Trash2 className="mr-1.5 size-3" /> Delete State
            </Button>
          </>
        )}

        {selectedEdge && (
          <>
            <div className="space-y-1.5">
              <Label className="text-xs">Action Name</Label>
              <Input
                value={(selectedEdge.label as string) || ''}
                onChange={(e) => onUpdateEdge(selectedEdge.id, { label: e.target.value })}
                placeholder="e.g. Approve, Reject"
                className="h-8 text-sm"
              />
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <p>From: <strong>{selectedEdge.source}</strong></p>
              <p>To: <strong>{selectedEdge.target}</strong></p>
            </div>
            <Button
              variant="destructive"
              size="sm"
              className="w-full"
              onClick={() => onDeleteEdge(selectedEdge.id)}
            >
              <Trash2 className="mr-1.5 size-3" /> Delete Transition
            </Button>
          </>
        )}
      </div>
    </div>
  );
}

// ── Workflow Card ─────────────────────────────────────────────────────
function WorkflowCard({ wf, onClick }: { wf: FrappeWorkflow; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col rounded-xl border bg-card p-5 text-left transition-all hover:border-primary/40 hover:shadow-md hover:shadow-primary/5"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10">
            <GitBranch className="size-4 text-primary" />
          </div>
          <h3 className="font-semibold text-sm truncate">{wf.name}</h3>
        </div>
        <Badge variant={wf.is_active ? 'default' : 'secondary'} className="text-[9px] h-4 px-1.5">
          {wf.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </div>

      <p className="text-xs text-muted-foreground mb-3">{wf.document_type}</p>

      {/* Mini flow preview */}
      <div className="flex items-center gap-1 overflow-hidden">
        {(wf.states || []).slice(0, 4).map((s, i) => (
          <div key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="size-3 text-muted-foreground/40 shrink-0" />}
            <div className={cn(
              'rounded-md px-2 py-0.5 text-[10px] font-medium shrink-0',
              STATUS_COLORS[s.doc_status]?.bg || 'bg-muted',
            )}>
              {s.state}
            </div>
          </div>
        ))}
        {(wf.states?.length || 0) > 4 && (
          <span className="text-[10px] text-muted-foreground">+{wf.states.length - 4}</span>
        )}
      </div>

      <div className="flex gap-3 mt-3 pt-3 border-t text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <CircleDot className="size-3" /> {wf.states?.length || 0} states
        </span>
        <span className="flex items-center gap-1">
          <ArrowRight className="size-3" /> {wf.transitions?.length || 0} transitions
        </span>
      </div>

      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-primary scale-x-0 group-hover:scale-x-100 transition-transform origin-left rounded-b-xl" />
    </button>
  );
}

// ── Main Component ───────────────────────────────────────────────────
export function WorkflowBuilder() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<'list' | 'canvas'>('list');
  const [workflowName, setWorkflowName] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [isNew, setIsNew] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const { data, isLoading } = useQuery({
    queryKey: ['frappe-workflows'],
    queryFn: async () => {
      const res = await api.getFrappeWorkflows();
      return res.workflows as FrappeWorkflow[];
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      const { states, transitions } = extractWorkflowData(nodes, edges);
      return api.saveFrappeWorkflow({
        workflow_name: workflowName,
        document_type: documentType,
        is_active: isActive ? 1 : 0,
        states,
        transitions,
      });
    },
    onSuccess: (res) => {
      toast.success(res.message || 'Workflow saved');
      queryClient.invalidateQueries({ queryKey: ['frappe-workflows'] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteWorkflow(name),
    onSuccess: () => {
      toast.success('Workflow deleted');
      queryClient.invalidateQueries({ queryKey: ['frappe-workflows'] });
      setView('list');
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const onConnect = useCallback((connection: Connection) => {
    setEdges(eds => addEdge({
      ...connection,
      label: 'Action',
      animated: true,
      style: { stroke: 'hsl(var(--primary))', strokeWidth: 2 },
      labelStyle: { fontSize: 11, fontWeight: 600, fill: 'hsl(var(--primary))' },
      labelBgStyle: { fill: 'hsl(var(--background))', strokeWidth: 0 },
      labelBgPadding: [6, 4] as [number, number],
      labelBgBorderRadius: 6,
      markerEnd: { type: MarkerType.ArrowClosed, color: 'hsl(var(--primary))' },
    }, eds));
  }, [setEdges]);

  const handleNew = () => {
    setIsNew(true);
    setWorkflowName('');
    setDocumentType('');
    setIsActive(true);
    setNodes([
      {
        id: 'Draft',
        type: 'stateNode',
        position: { x: 80, y: 180 },
        data: { label: 'Draft', doc_status: '0', allow_edit: 'All' },
      },
      {
        id: 'Approved',
        type: 'stateNode',
        position: { x: 420, y: 120 },
        data: { label: 'Approved', doc_status: '1', allow_edit: '' },
      },
      {
        id: 'Rejected',
        type: 'stateNode',
        position: { x: 420, y: 280 },
        data: { label: 'Rejected', doc_status: '0', allow_edit: 'All' },
      },
    ]);
    setEdges([
      {
        id: 'e-0',
        source: 'Draft',
        target: 'Approved',
        label: 'Approve',
        animated: true,
        style: { stroke: 'hsl(var(--primary))', strokeWidth: 2 },
        labelStyle: { fontSize: 11, fontWeight: 600, fill: 'hsl(var(--primary))' },
        labelBgStyle: { fill: 'hsl(var(--background))', strokeWidth: 0 },
        labelBgPadding: [6, 4] as [number, number],
        labelBgBorderRadius: 6,
        markerEnd: { type: MarkerType.ArrowClosed, color: 'hsl(var(--primary))' },
      },
      {
        id: 'e-1',
        source: 'Draft',
        target: 'Rejected',
        label: 'Reject',
        animated: true,
        style: { stroke: 'hsl(var(--primary))', strokeWidth: 2 },
        labelStyle: { fontSize: 11, fontWeight: 600, fill: 'hsl(var(--primary))' },
        labelBgStyle: { fill: 'hsl(var(--background))', strokeWidth: 0 },
        labelBgPadding: [6, 4] as [number, number],
        labelBgBorderRadius: 6,
        markerEnd: { type: MarkerType.ArrowClosed, color: 'hsl(var(--primary))' },
      },
    ]);
    setView('canvas');
  };

  const handleEdit = (wf: FrappeWorkflow) => {
    setIsNew(false);
    setWorkflowName(wf.name);
    setDocumentType(wf.document_type);
    setIsActive(!!wf.is_active);
    const { nodes: n, edges: e } = buildNodesAndEdges(wf.states || [], wf.transitions || []);
    setNodes(n);
    setEdges(e);
    setView('canvas');
  };

  const addNewNode = () => {
    const id = `State_${nodes.length + 1}`;
    setNodes(nds => [...nds, {
      id,
      type: 'stateNode',
      position: { x: 200 + Math.random() * 200, y: 150 + Math.random() * 150 },
      data: { label: id, doc_status: '0', allow_edit: 'All' },
    }]);
  };

  const handleNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  }, []);

  const handleEdgeClick = useCallback((_: any, edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
  }, []);

  const handlePaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
  }, []);

  const handleUpdateNode = (id: string, data: Record<string, any>) => {
    setNodes(nds => nds.map(n => {
      if (n.id === id) {
        // Also update the id if the label changed (states use label as id)
        const newId = data.label || n.id;
        if (newId !== n.id) {
          // Update edges that reference this node
          setEdges(eds => eds.map(e => ({
            ...e,
            source: e.source === n.id ? newId : e.source,
            target: e.target === n.id ? newId : e.target,
          })));
        }
        return { ...n, id: newId, data };
      }
      return n;
    }));
    // Update selection
    setSelectedNode(prev => prev && prev.id === id ? { ...prev, id: data.label || id, data } : prev);
  };

  const handleUpdateEdge = (id: string, updates: Partial<Edge>) => {
    setEdges(eds => eds.map(e => e.id === id ? { ...e, ...updates } : e));
    setSelectedEdge(prev => prev && prev.id === id ? { ...prev, ...updates } : prev);
  };

  const handleDeleteNode = (id: string) => {
    setNodes(nds => nds.filter(n => n.id !== id));
    setEdges(eds => eds.filter(e => e.source !== id && e.target !== id));
    setSelectedNode(null);
  };

  const handleDeleteEdge = (id: string) => {
    setEdges(eds => eds.filter(e => e.id !== id));
    setSelectedEdge(null);
  };

  // ── List View ──────────────────────────────────────────────────────
  if (view === 'list') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <GitBranch className="size-6 text-primary" />
              Workflow Builder
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Design visual workflows with states and transitions
            </p>
          </div>
          <Button onClick={handleNew} className="gap-1.5">
            <Plus className="size-4" /> New Workflow
          </Button>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-44 rounded-xl" />)}
          </div>
        ) : !data || data.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed p-16 space-y-4">
            <div className="flex size-16 items-center justify-center rounded-2xl bg-primary/10">
              <GitBranch className="size-8 text-primary" />
            </div>
            <div className="text-center">
              <h3 className="font-semibold mb-1">No Workflows Yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create your first visual workflow with drag-and-drop states
              </p>
              <Button onClick={handleNew}>
                <Plus className="mr-1.5 size-4" /> Create Workflow
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data.map(wf => (
              <WorkflowCard key={wf.name} wf={wf} onClick={() => handleEdit(wf)} />
            ))}
          </div>
        )}
      </div>
    );
  }

  // ── Canvas View ────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b bg-background/80 backdrop-blur-sm px-4 py-2.5 shrink-0">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" className="size-8" onClick={() => setView('list')}>
            <ArrowLeft className="size-4" />
          </Button>
          <div className="flex items-center gap-2">
            <Input
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="Workflow Name"
              className="h-8 w-48 text-sm font-semibold"
              disabled={!isNew}
            />
            <Input
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              placeholder="DocType"
              className="h-8 w-40 text-sm"
            />
            <div className="flex items-center gap-1.5 ml-2">
              <Switch
                checked={isActive}
                onCheckedChange={setIsActive}
                className="scale-75"
              />
              <span className="text-xs text-muted-foreground">
                {isActive ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={addNewNode}
          >
            <Plus className="size-3.5" /> Add State
          </Button>
          <Button
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => saveMutation.mutate()}
            disabled={!workflowName || !documentType || saveMutation.isPending}
          >
            <Save className="size-3.5" />
            {saveMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
          {!isNew && (
            <Button
              variant="destructive"
              size="sm"
              className="h-8"
              onClick={() => {
                if (confirm(`Delete "${workflowName}"?`)) {
                  deleteMutation.mutate(workflowName);
                }
              }}
            >
              <Trash2 className="size-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          onEdgeClick={handleEdgeClick}
          onPaneClick={handlePaneClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          defaultEdgeOptions={{
            animated: true,
            style: { strokeWidth: 2 },
          }}
          className="bg-muted/20"
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="hsl(var(--border))" />
          <Controls
            className="!border !rounded-lg !shadow-md !bg-background"
            showInteractive={false}
          />
          <MiniMap
            className="!border !rounded-lg !shadow-md !bg-background"
            nodeColor={() => 'hsl(var(--primary))'}
            maskColor="hsl(var(--muted) / 0.5)"
          />
        </ReactFlow>

        {/* Properties Panel */}
        <PropertiesPanel
          selectedNode={selectedNode}
          selectedEdge={selectedEdge}
          onUpdateNode={handleUpdateNode}
          onUpdateEdge={handleUpdateEdge}
          onDeleteNode={handleDeleteNode}
          onDeleteEdge={handleDeleteEdge}
          onClose={() => { setSelectedNode(null); setSelectedEdge(null); }}
        />

        {/* Help hint */}
        <div className="absolute bottom-4 left-4 z-10 flex items-center gap-3 rounded-lg bg-background/90 backdrop-blur-sm border px-3 py-2 text-[11px] text-muted-foreground shadow-sm">
          <span>Drag nodes to position</span>
          <span className="text-border">|</span>
          <span>Drag from handle to connect</span>
          <span className="text-border">|</span>
          <span>Click to edit properties</span>
        </div>
      </div>
    </div>
  );
}
