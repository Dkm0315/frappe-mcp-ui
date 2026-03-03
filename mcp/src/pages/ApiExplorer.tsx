/**
 * API Explorer Page
 * Interactive Frappe REST API testing and DocType introspection
 */
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useDocTypes, useDocTypeMeta } from '@/hooks/useDiscovery';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import {
  Terminal, Search, Play, Copy, X, Database,
  FileJson, List, FileText, Send, Clock,
} from 'lucide-react';

// ── DocType Selector ───────────────────────────────────────────────
function DoctypeSearch({
  value,
  onChange,
}: {
  value: string;
  onChange: (val: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const { data: doctypes, isLoading } = useDocTypes();

  const filtered = doctypes?.filter(
    (dt) => dt.name.toLowerCase().includes(search.toLowerCase())
  )?.slice(0, 30) || [];

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-3 size-4 text-muted-foreground" />
        <Input
          value={value || search}
          onChange={(e) => {
            setSearch(e.target.value);
            if (!e.target.value) onChange('');
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search for a DocType..."
          className="pl-9"
        />
        {value && (
          <button
            onClick={() => { onChange(''); setSearch(''); }}
            className="absolute right-3 top-3"
          >
            <X className="size-4 text-muted-foreground" />
          </button>
        )}
      </div>
      {open && !value && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-lg max-h-60 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-sm text-muted-foreground">Loading...</div>
            ) : filtered.length === 0 ? (
              <div className="p-4 text-sm text-muted-foreground">No DocTypes found</div>
            ) : (
              filtered.map((dt) => (
                <button
                  key={dt.name}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-accent"
                  onClick={() => {
                    onChange(dt.name);
                    setSearch('');
                    setOpen(false);
                  }}
                >
                  <span className="font-medium">{dt.name}</span>
                  <span className="ml-2 text-xs text-muted-foreground">{dt.module}</span>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ── API Call History Item ──────────────────────────────────────────
interface ApiCallRecord {
  id: string;
  method: string;
  url: string;
  params: any;
  response: any;
  status: 'success' | 'error';
  duration: number;
  timestamp: Date;
}

// ── Main Page ──────────────────────────────────────────────────────
export function ApiExplorer() {
  const [selectedDoctype, setSelectedDoctype] = useState('');
  const [apiMethod, setApiMethod] = useState('get_list');
  const [filters, setFilters] = useState('{}');
  const [fields, setFields] = useState('["name", "modified"]');
  const [limit, setLimit] = useState('20');
  const [documentName, setDocumentName] = useState('');
  const [customMethod, setCustomMethod] = useState('');
  const [customArgs, setCustomArgs] = useState('{}');
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<ApiCallRecord[]>([]);

  const { data: meta, isLoading: metaLoading } = useDocTypeMeta(selectedDoctype);

  const executeMutation = useMutation({
    mutationFn: async () => {
      const startTime = Date.now();
      let response: any;
      let url = '';

      if (apiMethod === 'get_list') {
        url = `frappe.client.get_list`;
        response = await api.call('frappe.client.get_list', {
          doctype: selectedDoctype,
          filters: JSON.parse(filters),
          fields: JSON.parse(fields),
          limit_page_length: parseInt(limit),
        });
      } else if (apiMethod === 'get_document') {
        url = `frappe.client.get`;
        response = await api.call('frappe.client.get', {
          doctype: selectedDoctype,
          name: documentName,
        });
      } else if (apiMethod === 'get_count') {
        url = `frappe.client.get_count`;
        response = await api.call('frappe.client.get_count', {
          doctype: selectedDoctype,
          filters: JSON.parse(filters),
        });
      } else if (apiMethod === 'custom') {
        url = customMethod;
        response = await api.call(customMethod, JSON.parse(customArgs));
      }

      const duration = Date.now() - startTime;
      return { response, url, duration };
    },
    onSuccess: ({ response, url, duration }) => {
      setResult(response);
      const record: ApiCallRecord = {
        id: Math.random().toString(36).substring(2, 9),
        method: apiMethod,
        url,
        params: apiMethod === 'custom' ? customArgs : { doctype: selectedDoctype, filters, fields, limit },
        response,
        status: 'success',
        duration,
        timestamp: new Date(),
      };
      setHistory((prev) => [record, ...prev].slice(0, 20));
      toast.success(`API call completed in ${duration}ms`);
    },
    onError: (err: Error) => {
      const record: ApiCallRecord = {
        id: Math.random().toString(36).substring(2, 9),
        method: apiMethod,
        url: '',
        params: {},
        response: err.message,
        status: 'error',
        duration: 0,
        timestamp: new Date(),
      };
      setHistory((prev) => [record, ...prev].slice(0, 20));
      setResult({ error: err.message });
      toast.error(err.message);
    },
  });

  const canExecute = apiMethod === 'custom'
    ? !!customMethod
    : apiMethod === 'get_document'
      ? !!selectedDoctype && !!documentName
      : !!selectedDoctype;

  const copyResult = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    toast.success('Copied to clipboard');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Terminal className="size-8 text-primary" />
          API Explorer
        </h1>
        <p className="mt-2 text-muted-foreground">
          Test Frappe REST API calls interactively
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Request Builder */}
        <div className="space-y-4">
          {/* Method Selector */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">API Method</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {['get_list', 'get_document', 'get_count', 'custom'].map((m) => (
                  <Button
                    key={m}
                    variant={apiMethod === m ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setApiMethod(m)}
                  >
                    {m === 'get_list' && <List className="mr-1 size-3" />}
                    {m === 'get_document' && <FileText className="mr-1 size-3" />}
                    {m === 'get_count' && <Database className="mr-1 size-3" />}
                    {m === 'custom' && <Send className="mr-1 size-3" />}
                    {m.replace('_', ' ')}
                  </Button>
                ))}
              </div>

              {apiMethod !== 'custom' && (
                <div>
                  <Label>DocType</Label>
                  <DoctypeSearch value={selectedDoctype} onChange={setSelectedDoctype} />
                </div>
              )}

              {apiMethod === 'get_list' && (
                <>
                  <div>
                    <Label>Filters (JSON)</Label>
                    <Textarea
                      value={filters}
                      onChange={(e) => setFilters(e.target.value)}
                      placeholder='{"status": "Open"}'
                      className="font-mono text-sm min-h-[60px]"
                    />
                  </div>
                  <div>
                    <Label>Fields (JSON array)</Label>
                    <Input
                      value={fields}
                      onChange={(e) => setFields(e.target.value)}
                      placeholder='["name", "status", "modified"]'
                      className="font-mono text-sm"
                    />
                  </div>
                  <div>
                    <Label>Limit</Label>
                    <Input
                      value={limit}
                      onChange={(e) => setLimit(e.target.value)}
                      type="number"
                      className="w-24"
                    />
                  </div>
                </>
              )}

              {apiMethod === 'get_document' && (
                <div>
                  <Label>Document Name</Label>
                  <Input
                    value={documentName}
                    onChange={(e) => setDocumentName(e.target.value)}
                    placeholder="e.g. SALES-001"
                  />
                </div>
              )}

              {apiMethod === 'get_count' && (
                <div>
                  <Label>Filters (JSON)</Label>
                  <Textarea
                    value={filters}
                    onChange={(e) => setFilters(e.target.value)}
                    placeholder='{"status": "Open"}'
                    className="font-mono text-sm min-h-[60px]"
                  />
                </div>
              )}

              {apiMethod === 'custom' && (
                <>
                  <div>
                    <Label>Method</Label>
                    <Input
                      value={customMethod}
                      onChange={(e) => setCustomMethod(e.target.value)}
                      placeholder="frappe.client.get_list"
                      className="font-mono text-sm"
                    />
                  </div>
                  <div>
                    <Label>Arguments (JSON)</Label>
                    <Textarea
                      value={customArgs}
                      onChange={(e) => setCustomArgs(e.target.value)}
                      placeholder='{"doctype": "User"}'
                      className="font-mono text-sm min-h-[80px]"
                    />
                  </div>
                </>
              )}

              <Button
                className="w-full"
                onClick={() => executeMutation.mutate()}
                disabled={!canExecute || executeMutation.isPending}
              >
                {executeMutation.isPending ? (
                  <>
                    <Clock className="mr-2 size-4 animate-spin" /> Executing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 size-4" /> Execute
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* DocType Schema */}
          {selectedDoctype && apiMethod !== 'custom' && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Database className="size-4" />
                  {selectedDoctype} Fields
                </CardTitle>
              </CardHeader>
              <CardContent>
                {metaLoading ? (
                  <Skeleton className="h-32" />
                ) : meta?.fields ? (
                  <ScrollArea className="h-48">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fieldname</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Label</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {meta.fields
                          .filter((f: any) => !['Section Break', 'Column Break', 'Tab Break'].includes(f.fieldtype))
                          .map((f: any) => (
                            <TableRow key={f.fieldname}>
                              <TableCell>
                                <code className="text-xs">{f.fieldname}</code>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className="text-[10px]">{f.fieldtype}</Badge>
                              </TableCell>
                              <TableCell className="text-xs text-muted-foreground">{f.label}</TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                ) : (
                  <p className="text-sm text-muted-foreground">No schema available</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Response + History */}
        <div className="space-y-4">
          {/* Response */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileJson className="size-4" /> Response
                </CardTitle>
                {result && (
                  <Button size="sm" variant="outline" onClick={copyResult}>
                    <Copy className="mr-1 size-3" /> Copy
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {result ? (
                <ScrollArea className="h-[300px]">
                  <pre className="rounded bg-muted p-3 text-xs font-mono overflow-x-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </ScrollArea>
              ) : (
                <div className="flex h-32 items-center justify-center text-muted-foreground">
                  <p className="text-sm">Execute an API call to see results</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* History */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="size-4" /> Recent Calls ({history.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-4">No calls yet</p>
              ) : (
                <ScrollArea className="h-48">
                  <div className="space-y-2">
                    {history.map((h) => (
                      <button
                        key={h.id}
                        className="w-full rounded border p-2 text-left hover:bg-accent transition-colors"
                        onClick={() => setResult(h.response)}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">{h.method}</span>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={h.status === 'success' ? 'default' : 'destructive'}
                              className="text-[10px]"
                            >
                              {h.status}
                            </Badge>
                            <span className="text-[10px] text-muted-foreground">{h.duration}ms</span>
                          </div>
                        </div>
                        <span className="text-[10px] text-muted-foreground">
                          {h.timestamp.toLocaleTimeString()}
                        </span>
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
