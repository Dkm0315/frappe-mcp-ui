/**
 * ToolExecutor Component
 * Modal for executing MCP tools with SMART FORMS
 *
 * Uses a simple div-based modal instead of Radix Dialog to avoid
 * React 19 infinite loop (Radix Presence setNode -> setState -> re-render loop).
 *
 * DocType dropdown uses fixed positioning to avoid modal overflow clipping.
 */
import { useState, useEffect, useLayoutEffect, useMemo, useCallback, useRef, Component, type ReactNode, type ErrorInfo } from 'react';
import { createPortal } from 'react-dom';
import { useExecuteTool } from '@/hooks/useExecuteTool';
import { SmartForm } from './SmartForm';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { AlertTriangle, Coins, Loader2, CheckCircle2, Sparkles, Search, X, Copy, Check } from 'lucide-react';
import { useDocTypes } from '@/hooks/useDiscovery';
import type { MCPTool } from '@/types';

// ── Error Boundary ──────────────────────────────────────────────────
class ToolErrorBoundary extends Component<
  { children: ReactNode; onReset: () => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode; onReset: () => void }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ToolExecutor error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center space-y-3">
          <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
          <p className="font-medium text-sm">Something went wrong rendering this tool.</p>
          <p className="text-xs text-muted-foreground">{this.state.error?.message}</p>
          <Button variant="outline" size="sm" onClick={() => {
            this.setState({ hasError: false, error: null });
            this.props.onReset();
          }}>
            Try Again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Portal-Based DocType Selector ───────────────────────────────────
// Uses createPortal + useLayoutEffect for reliable positioning outside modal overflow.
function DocTypeSelector({
  value,
  onChange,
  doctypes,
  placeholder = 'Search and select a DocType...',
}: {
  value: string;
  onChange: (val: string) => void;
  doctypes: Array<{ name: string; module: string }> | undefined;
  placeholder?: string;
}) {
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [posReady, setPosReady] = useState(false);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 });

  // Recalculate position synchronously before paint
  const recalcPos = useCallback(() => {
    if (!inputRef.current) return;
    const rect = inputRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const dropdownHeight = 240;
    const showAbove = spaceBelow < dropdownHeight && rect.top > dropdownHeight;
    setDropdownPos({
      top: showAbove ? rect.top - dropdownHeight - 4 : rect.bottom + 4,
      left: rect.left,
      width: rect.width,
    });
    setPosReady(true);
  }, []);

  // useLayoutEffect fires synchronously before browser paints — no flash
  useLayoutEffect(() => {
    if (!isOpen) { setPosReady(false); return; }
    recalcPos();
  }, [isOpen, search, recalcPos]);

  // Reposition on scroll (inside the modal's overflow container) and resize
  useEffect(() => {
    if (!isOpen) return;
    const handleReposition = () => recalcPos();
    window.addEventListener('resize', handleReposition);
    window.addEventListener('scroll', handleReposition, true); // capture phase for inner scrolls
    return () => {
      window.removeEventListener('resize', handleReposition);
      window.removeEventListener('scroll', handleReposition, true);
    };
  }, [isOpen, recalcPos]);

  const filtered = useMemo(() => {
    if (!doctypes) return [];
    if (!search) return doctypes.slice(0, 80);
    const q = search.toLowerCase();
    return doctypes.filter(
      (dt) => dt.name.toLowerCase().includes(q) || dt.module.toLowerCase().includes(q)
    ).slice(0, 80);
  }, [doctypes, search]);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        inputRef.current && !inputRef.current.contains(target) &&
        dropdownRef.current && !dropdownRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen]);

  const showDropdown = isOpen && posReady && filtered.length > 0;
  const showEmpty = isOpen && posReady && search && filtered.length === 0;

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="pl-9"
        />
      </div>
      {value && (
        <div className="mt-1.5 flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">{value}</Badge>
          <button
            type="button"
            onClick={() => { onChange(''); setSearch(''); }}
            className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear
          </button>
        </div>
      )}
      {/* Portal dropdown rendered at document.body to escape modal overflow */}
      {showDropdown && createPortal(
        <div
          ref={dropdownRef}
          className="fixed z-[9999] rounded-lg border bg-popover shadow-xl max-h-60 overflow-y-auto"
          style={{ top: dropdownPos.top, left: dropdownPos.left, width: dropdownPos.width }}
        >
          {filtered.map((dt) => (
            <button
              key={dt.name}
              type="button"
              className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
              onClick={() => {
                onChange(dt.name);
                setSearch('');
                setIsOpen(false);
              }}
            >
              <span className={cn('truncate', value === dt.name && 'font-medium text-primary')}>{dt.name}</span>
              <span className="ml-2 shrink-0 text-[10px] text-muted-foreground">{dt.module}</span>
            </button>
          ))}
        </div>,
        document.body
      )}
      {showEmpty && createPortal(
        <div
          className="fixed z-[9999] rounded-lg border bg-popover shadow-xl p-4 text-center text-sm text-muted-foreground"
          style={{ top: dropdownPos.top, left: dropdownPos.left, width: dropdownPos.width }}
        >
          No DocType found matching &ldquo;{search}&rdquo;
        </div>,
        document.body
      )}
    </div>
  );
}

// ── Result Viewer ───────────────────────────────────────────────────
function ResultViewer({ result }: { result: any }) {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(result, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(json);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="flex size-6 items-center justify-center rounded-full bg-emerald-500/10">
          <CheckCircle2 className="size-3.5 text-emerald-500" />
        </div>
        <span className="text-sm font-medium text-emerald-600">Execution Successful</span>
      </div>
      <div className="relative rounded-lg bg-muted/60 border">
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 flex items-center gap-1 rounded-md bg-background/80 px-2 py-1 text-[10px] text-muted-foreground hover:text-foreground border transition-colors"
        >
          {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
        <pre className="p-4 text-xs overflow-x-auto max-h-80 overflow-y-auto leading-relaxed">
          {json}
        </pre>
      </div>
    </div>
  );
}

// ── Main ToolExecutor ───────────────────────────────────────────────
interface ToolExecutorProps {
  tool: MCPTool;
  open: boolean;
  onClose: () => void;
  initialParams?: Record<string, any>;
}

const EMPTY_PARAMS: Record<string, any> = {};

export function ToolExecutor({ tool, open, onClose, initialParams }: ToolExecutorProps) {
  const stableInitial = initialParams ?? EMPTY_PARAMS;
  const [params, setParams] = useState<Record<string, any>>(stableInitial);
  const [result, setResult] = useState<any>(null);
  const [showSmartForm, setShowSmartForm] = useState(false);
  const executeMutation = useExecuteTool();
  const { data: doctypes } = useDocTypes();

  const initialKeys = initialParams ? Object.keys(initialParams).join(',') : '';
  useEffect(() => {
    if (initialParams && Object.keys(initialParams).length > 0) {
      setParams(initialParams);
    }
  }, [initialKeys]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = ''; };
    }
  }, [open]);

  const handleExecute = () => {
    executeMutation.mutate(
      { toolName: tool.name, params },
      {
        onSuccess: (data) => {
          setResult(data.result);
        },
      }
    );
  };

  const handleClose = useCallback(() => {
    setParams({});
    setResult(null);
    setShowSmartForm(false);
    executeMutation.reset();
    onClose();
  }, [onClose, executeMutation]);

  const updateParam = (key: string, value: any) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleSmartFormChange = (values: Record<string, any>) => {
    setParams(prev => ({ ...prev, data: values }));
  };

  const needsDocTypeSelection = (tool.name === 'create_document' || tool.name === 'update_document') && !showSmartForm;
  const canUseSmartForm = (tool.name === 'create_document' || tool.name === 'update_document') && params.doctype;

  if (!open) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="tool-executor-title"
        className="fixed top-[50%] left-[50%] z-50 w-full max-w-2xl translate-x-[-50%] translate-y-[-50%] rounded-xl border bg-background shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b px-6 py-4">
          <div className="space-y-1.5 pr-8">
            <h2 id="tool-executor-title" className="text-base font-semibold flex items-center gap-2">
              {canUseSmartForm && <Sparkles className="size-4 text-primary" />}
              {tool.title}
              {tool.destructive && <AlertTriangle className="size-4 text-red-500" />}
            </h2>
            <p className="text-xs text-muted-foreground">{tool.description}</p>
            <div className="flex gap-1.5 pt-1">
              <Badge variant="outline" className="text-[10px] h-5">{tool.category}</Badge>
              <Badge variant="secondary" className="text-[10px] h-5 gap-1">
                <Coins className="size-2.5" />
                {tool.base_cost} credits
              </Badge>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <X className="size-4" />
          </button>
        </div>

        {tool.destructive && !result && (
          <div className="mx-6 mt-4">
            <Alert variant="destructive" className="border-red-500/20 bg-red-500/5">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                This is a destructive operation. Please proceed with caution.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Body */}
        <ToolErrorBoundary onReset={handleClose}>
          <div className="max-h-[60vh] overflow-y-auto px-6 py-4">
            {result ? (
              <ResultViewer result={result} />
            ) : (
              <div className="space-y-4">
                {/* DocType Selection for Create/Update */}
                {needsDocTypeSelection && (
                  <div className="space-y-1.5">
                    <Label className="text-xs">
                      Select Document Type
                      <span className="ml-1 text-red-500">*</span>
                    </Label>
                    <DocTypeSelector
                      value={params.doctype || ''}
                      onChange={(val) => {
                        updateParam('doctype', val);
                        if (val) setShowSmartForm(true);
                      }}
                      doctypes={doctypes}
                      placeholder="Search DocTypes to create..."
                    />
                    <p className="text-[11px] text-muted-foreground">
                      Select a document type to see user-friendly form fields
                    </p>
                  </div>
                )}

                {/* Smart Form for Create/Update */}
                {canUseSmartForm && showSmartForm && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 rounded-lg bg-primary/5 border border-primary/10 p-3">
                      <Sparkles className="size-3.5 text-primary" />
                      <p className="text-xs font-medium">Smart Form for {params.doctype}</p>
                    </div>
                    <SmartForm
                      doctype={params.doctype}
                      initialValues={params.data || {}}
                      onChange={handleSmartFormChange}
                    />
                  </div>
                )}

                {/* Simple Fields for Other Tools */}
                {!needsDocTypeSelection && !canUseSmartForm && (
                  <div className="space-y-4">
                    {(tool.name.includes('document') || tool.name.includes('get_list') ||
                      tool.name.includes('search') || tool.name.includes('dashboard')) && (
                      <div className="space-y-1.5">
                        <Label className="text-xs">
                          Document Type
                          <span className="ml-1 text-red-500">*</span>
                        </Label>
                        <DocTypeSelector
                          value={params.doctype || ''}
                          onChange={(val) => updateParam('doctype', val)}
                          doctypes={doctypes}
                        />
                      </div>
                    )}

                    {(tool.name === 'get_document' || tool.name === 'update_document' || tool.name === 'delete_document') && (
                      <div className="space-y-1.5">
                        <Label htmlFor="name" className="text-xs">
                          Document ID / Name
                          <span className="ml-1 text-red-500">*</span>
                        </Label>
                        <Input
                          id="name"
                          value={params.name || ''}
                          onChange={(e) => updateParam('name', e.target.value)}
                          placeholder="Enter document name or ID"
                        />
                      </div>
                    )}

                    {tool.name === 'search_documents' && (
                      <div className="space-y-1.5">
                        <Label htmlFor="search_text" className="text-xs">
                          Search For
                          <span className="ml-1 text-red-500">*</span>
                        </Label>
                        <Input
                          id="search_text"
                          value={params.search_text || ''}
                          onChange={(e) => updateParam('search_text', e.target.value)}
                          placeholder="What are you looking for?"
                        />
                      </div>
                    )}

                    {(tool.name === 'get_list' || tool.name === 'search_documents' || tool.name === 'export_data') && (
                      <div className="space-y-1.5">
                        <Label htmlFor="limit" className="text-xs">Maximum Results</Label>
                        <Input
                          id="limit"
                          type="number"
                          value={params.limit || 20}
                          onChange={(e) => updateParam('limit', parseInt(e.target.value))}
                          min="1"
                          max="100"
                        />
                      </div>
                    )}

                    {tool.name === 'execute_report' && (
                      <div className="space-y-1.5">
                        <Label htmlFor="report_name" className="text-xs">
                          Report Name
                          <span className="ml-1 text-red-500">*</span>
                        </Label>
                        <Input
                          id="report_name"
                          value={params.report_name || ''}
                          onChange={(e) => updateParam('report_name', e.target.value)}
                          placeholder="Enter report name"
                        />
                      </div>
                    )}

                    {tool.name === 'bulk_update' && (
                      <div className="space-y-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="filters" className="text-xs">Filters (JSON)</Label>
                          <Input
                            id="filters"
                            value={params.filters || ''}
                            onChange={(e) => updateParam('filters', e.target.value)}
                            placeholder='e.g., {"status": "Open"}'
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="update_data" className="text-xs">Update Data (JSON)</Label>
                          <Input
                            id="update_data"
                            value={params.update_data || ''}
                            onChange={(e) => updateParam('update_data', e.target.value)}
                            placeholder='e.g., {"status": "Closed"}'
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </ToolErrorBoundary>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t px-6 py-3">
          {result ? (
            <Button onClick={handleClose} size="sm">Done</Button>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleExecute}
                disabled={executeMutation.isPending || (needsDocTypeSelection && !params.doctype)}
                variant={tool.destructive ? 'destructive' : 'default'}
              >
                {executeMutation.isPending ? (
                  <>
                    <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                    Executing...
                  </>
                ) : (
                  'Execute'
                )}
              </Button>
            </>
          )}
        </div>
      </div>
    </>
  );
}
