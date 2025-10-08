/**
 * ToolExecutor Component
 * Modal for executing MCP tools with SMART FORMS - NO JSON REQUIRED!
 */
import { useState, useEffect } from 'react';
import { useExecuteTool } from '@/hooks/useExecuteTool';
import { SmartForm } from './SmartForm';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { AlertTriangle, Coins, Loader2, CheckCircle2, Sparkles, Search, Check, ChevronsUpDown } from 'lucide-react';
import { useDocTypes } from '@/hooks/useDiscovery';
import { cn } from '@/lib/utils';
import type { MCPTool } from '@/types';

interface ToolExecutorProps {
  tool: MCPTool;
  open: boolean;
  onClose: () => void;
  initialParams?: Record<string, any>;
}

export function ToolExecutor({ tool, open, onClose, initialParams = {} }: ToolExecutorProps) {
  const [params, setParams] = useState<Record<string, any>>(initialParams);
  const [result, setResult] = useState<any>(null);
  const [showSmartForm, setShowSmartForm] = useState(false);
  const [docTypeOpen, setDocTypeOpen] = useState(false);
  const executeMutation = useExecuteTool();
  const { data: doctypes } = useDocTypes();

  useEffect(() => {
    setParams(initialParams);
  }, [initialParams]);

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

  const handleClose = () => {
    setParams({});
    setResult(null);
    setShowSmartForm(false);
    executeMutation.reset();
    onClose();
  };

  const updateParam = (key: string, value: any) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleSmartFormChange = (values: Record<string, any>) => {
    setParams(prev => ({ ...prev, data: values }));
  };

  // Check if we should show smart form
  const needsDocTypeSelection = (tool.name === 'create_document' || tool.name === 'update_document') && !showSmartForm;
  const canUseSmartForm = (tool.name === 'create_document' || tool.name === 'update_document') && params.doctype;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {canUseSmartForm && <Sparkles className="h-5 w-5 text-primary" />}
            {tool.title}
            {tool.destructive && <AlertTriangle className="h-5 w-5 text-red-600" />}
          </DialogTitle>
          <DialogDescription>{tool.description}</DialogDescription>
          <div className="flex gap-2 pt-2">
            <Badge variant="outline">{tool.category}</Badge>
            <Badge variant="secondary" className="gap-1">
              <Coins className="h-3 w-3" />
              {tool.base_cost} credits
            </Badge>
          </div>
        </DialogHeader>

        {tool.destructive && !result && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              This is a destructive operation. Please proceed with caution.
            </AlertDescription>
          </Alert>
        )}

        <ScrollArea className="max-h-[500px]">
          {result ? (
            <div className="space-y-4 p-1">
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-medium">Execution Successful</span>
              </div>
              <div className="rounded-lg bg-muted p-4">
                <pre className="text-xs overflow-x-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="space-y-6 p-1">
              {/* DocType Selection for Create/Update */}
              {needsDocTypeSelection && (
                <div className="space-y-2">
                  <Label htmlFor="doctype">
                    Select Document Type
                    <span className="ml-1 text-red-600">*</span>
                  </Label>
                  <Popover open={docTypeOpen} onOpenChange={setDocTypeOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={docTypeOpen}
                        className="w-full justify-between"
                      >
                        {params.doctype || "Choose what you want to create..."}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-full p-0" align="start">
                      <Command>
                        <CommandInput placeholder="Search DocTypes..." />
                        <CommandList>
                          <CommandEmpty>No DocType found.</CommandEmpty>
                          <CommandGroup>
                            {doctypes?.map((dt) => (
                              <CommandItem
                                key={dt.name}
                                value={dt.name}
                                onSelect={(currentValue) => {
                                  updateParam('doctype', currentValue);
                                  setShowSmartForm(true);
                                  setDocTypeOpen(false);
                                }}
                              >
                                <Check
                                  className={cn(
                                    "mr-2 h-4 w-4",
                                    params.doctype === dt.name ? "opacity-100" : "opacity-0"
                                  )}
                                />
                                <span className="flex-1">{dt.name}</span>
                                <Badge variant="secondary" className="ml-2 text-xs">
                                  {dt.module}
                                </Badge>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                  <p className="text-xs text-muted-foreground">
                    💡 Select a document type to see user-friendly form fields
                  </p>
                </div>
              )}

              {/* Smart Form for Create/Update */}
              {canUseSmartForm && showSmartForm && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 rounded-lg bg-primary/10 p-3">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <p className="text-sm font-medium">
                      Smart Form for {params.doctype}
                    </p>
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
                  {/* DocType field for other tools */}
                  {(tool.name.includes('document') || tool.name.includes('get_list') || 
                    tool.name.includes('search') || tool.name.includes('dashboard')) && (
                    <div className="space-y-2">
                      <Label htmlFor="doctype">
                        Document Type
                        <span className="ml-1 text-red-600">*</span>
                      </Label>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            variant="outline"
                            role="combobox"
                            className="w-full justify-between"
                          >
                            {params.doctype || "Select document type..."}
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-full p-0" align="start">
                          <Command>
                            <CommandInput placeholder="Search DocTypes..." />
                            <CommandList>
                              <CommandEmpty>No DocType found.</CommandEmpty>
                              <CommandGroup>
                                {doctypes?.map((dt) => (
                                  <CommandItem
                                    key={dt.name}
                                    value={dt.name}
                                    onSelect={(currentValue) => {
                                      updateParam('doctype', currentValue);
                                    }}
                                  >
                                    <Check
                                      className={cn(
                                        "mr-2 h-4 w-4",
                                        params.doctype === dt.name ? "opacity-100" : "opacity-0"
                                      )}
                                    />
                                    <span className="flex-1">{dt.name}</span>
                                    <Badge variant="secondary" className="ml-2 text-xs">
                                      {dt.module}
                                    </Badge>
                                  </CommandItem>
                                ))}
                              </CommandGroup>
                            </CommandList>
                          </Command>
                        </PopoverContent>
                      </Popover>
                    </div>
                  )}

                  {/* Name field */}
                  {(tool.name === 'get_document' || tool.name === 'update_document' || tool.name === 'delete_document') && (
                    <div className="space-y-2">
                      <Label htmlFor="name">
                        Document ID / Name
                        <span className="ml-1 text-red-600">*</span>
                      </Label>
                      <Input
                        id="name"
                        value={params.name || ''}
                        onChange={(e) => updateParam('name', e.target.value)}
                        placeholder="Enter document name or ID"
                      />
                    </div>
                  )}

                  {/* Search text */}
                  {tool.name === 'search_documents' && (
                    <div className="space-y-2">
                      <Label htmlFor="search_text">
                        Search For
                        <span className="ml-1 text-red-600">*</span>
                      </Label>
                      <Input
                        id="search_text"
                        value={params.search_text || ''}
                        onChange={(e) => updateParam('search_text', e.target.value)}
                        placeholder="What are you looking for?"
                      />
                    </div>
                  )}

                  {/* Limit field */}
                  {(tool.name === 'get_list' || tool.name === 'search_documents' || tool.name === 'export_data') && (
                    <div className="space-y-2">
                      <Label htmlFor="limit">Maximum Results</Label>
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

                  {/* Report name */}
                  {tool.name === 'execute_report' && (
                    <div className="space-y-2">
                      <Label htmlFor="report_name">
                        Report Name
                        <span className="ml-1 text-red-600">*</span>
                      </Label>
                      <Input
                        id="report_name"
                        value={params.report_name || ''}
                        onChange={(e) => updateParam('report_name', e.target.value)}
                        placeholder="Enter report name"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </ScrollArea>

        <DialogFooter>
          {result ? (
            <Button onClick={handleClose}>Close</Button>
          ) : (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleExecute}
                disabled={executeMutation.isPending || (needsDocTypeSelection && !params.doctype)}
                variant={tool.destructive ? 'destructive' : 'default'}
              >
                {executeMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>Execute</>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

