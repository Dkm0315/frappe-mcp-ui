/**
 * Schema Manager Page
 * Manage Custom Fields and Property Setters for DocTypes
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useDocTypes } from '@/hooks/useDiscovery';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import {
  Database, Plus, Trash2, Search, Settings2, Columns3, X, Save,
} from 'lucide-react';

const FIELD_TYPES = [
  'Data', 'Link', 'Dynamic Link', 'Password', 'Int', 'Float', 'Currency',
  'Percent', 'Check', 'Small Text', 'Long Text', 'Text', 'Text Editor',
  'Code', 'HTML Editor', 'Markdown Editor', 'Date', 'Datetime', 'Time',
  'Duration', 'Select', 'Rating', 'Attach', 'Attach Image', 'Color',
  'Barcode', 'Geolocation', 'Phone', 'Autocomplete', 'Read Only',
  'Section Break', 'Column Break', 'Tab Break', 'Table', 'Table MultiSelect',
  'Image', 'Heading', 'HTML', 'Button', 'Signature', 'Icon', 'JSON',
];

// ── DocType Selector ───────────────────────────────────────────────
function DocTypeSearch({
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

// ── Custom Fields Tab ──────────────────────────────────────────────
function CustomFieldsTab({ doctype }: { doctype: string }) {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    label: '', fieldtype: 'Data', options: '', insert_after: '',
    reqd: 0, hidden: 0, default: '', description: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['ide-custom-fields', doctype],
    queryFn: async () => {
      const res = await api.getCustomFieldsForDoctype(doctype);
      return res.fields as any[];
    },
    enabled: !!doctype,
  });

  const addMutation = useMutation({
    mutationFn: () => api.addCustomField({ dt: doctype, ...form }),
    onSuccess: (res) => {
      toast.success(res.message || 'Custom Field added');
      queryClient.invalidateQueries({ queryKey: ['ide-custom-fields', doctype] });
      setShowAdd(false);
      setForm({ label: '', fieldtype: 'Data', options: '', insert_after: '', reqd: 0, hidden: 0, default: '', description: '' });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.deleteCustomField(name),
    onSuccess: () => {
      toast.success('Custom Field deleted');
      queryClient.invalidateQueries({ queryKey: ['ide-custom-fields', doctype] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (!doctype) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground">
        Select a DocType above to manage custom fields
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          Custom Fields for {doctype} ({data?.length || 0})
        </h3>
        <Button size="sm" variant="outline" onClick={() => setShowAdd(!showAdd)}>
          {showAdd ? <X className="mr-1 size-3" /> : <Plus className="mr-1 size-3" />}
          {showAdd ? 'Cancel' : 'Add Field'}
        </Button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <Label>Label</Label>
                <Input
                  value={form.label}
                  onChange={(e) => setForm({ ...form, label: e.target.value })}
                  placeholder="e.g. Custom Status"
                />
              </div>
              <div>
                <Label>Field Type</Label>
                <select
                  value={form.fieldtype}
                  onChange={(e) => setForm({ ...form, fieldtype: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {FIELD_TYPES.map((ft) => (
                    <option key={ft} value={ft}>{ft}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Options</Label>
                <Input
                  value={form.options}
                  onChange={(e) => setForm({ ...form, options: e.target.value })}
                  placeholder="Link DocType or select options"
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <Label>Insert After</Label>
                <Input
                  value={form.insert_after}
                  onChange={(e) => setForm({ ...form, insert_after: e.target.value })}
                  placeholder="fieldname"
                />
              </div>
              <div>
                <Label>Default Value</Label>
                <Input
                  value={form.default}
                  onChange={(e) => setForm({ ...form, default: e.target.value })}
                />
              </div>
              <div className="flex items-end gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={!!form.reqd}
                    onCheckedChange={(c) => setForm({ ...form, reqd: c ? 1 : 0 })}
                  />
                  <Label>Required</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={!!form.hidden}
                    onCheckedChange={(c) => setForm({ ...form, hidden: c ? 1 : 0 })}
                  />
                  <Label>Hidden</Label>
                </div>
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Help text shown below the field"
              />
            </div>
            <Button
              onClick={() => addMutation.mutate()}
              disabled={!form.label || addMutation.isPending}
            >
              <Save className="mr-2 size-4" />
              {addMutation.isPending ? 'Adding...' : 'Add Custom Field'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Fields Table */}
      {isLoading ? (
        <Skeleton className="h-48" />
      ) : !data || data.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No custom fields for this DocType
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Label</TableHead>
                  <TableHead>Fieldname</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Options</TableHead>
                  <TableHead>Required</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((f: any) => (
                  <TableRow key={f.name}>
                    <TableCell className="font-medium">{f.label}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-1 py-0.5 rounded">{f.fieldname}</code>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{f.fieldtype}</Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-32 truncate">
                      {f.options || '-'}
                    </TableCell>
                    <TableCell>{f.reqd ? 'Yes' : 'No'}</TableCell>
                    <TableCell>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="size-7"
                        onClick={() => {
                          if (confirm(`Delete field "${f.label}"?`)) {
                            deleteMutation.mutate(f.name);
                          }
                        }}
                      >
                        <Trash2 className="size-3" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Property Setters Tab ───────────────────────────────────────────
function PropertySettersTab({ doctype }: { doctype: string }) {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    field_name: '', property: '', value: '', property_type: 'Data',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['property-setters', doctype],
    queryFn: async () => {
      const res = await api.getPropertySetters(doctype);
      return res.property_setters as any[];
    },
    enabled: !!doctype,
  });

  const saveMutation = useMutation({
    mutationFn: () => api.setProperty({ doc_type: doctype, ...form }),
    onSuccess: (res) => {
      toast.success(res.message || 'Property set');
      queryClient.invalidateQueries({ queryKey: ['property-setters', doctype] });
      setShowAdd(false);
      setForm({ field_name: '', property: '', value: '', property_type: 'Data' });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (!doctype) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground">
        Select a DocType above to manage property setters
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          Property Setters for {doctype} ({data?.length || 0})
        </h3>
        <Button size="sm" variant="outline" onClick={() => setShowAdd(!showAdd)}>
          {showAdd ? <X className="mr-1 size-3" /> : <Plus className="mr-1 size-3" />}
          {showAdd ? 'Cancel' : 'Set Property'}
        </Button>
      </div>

      {/* Add Form */}
      {showAdd && (
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label>Field Name</Label>
                <Input
                  value={form.field_name}
                  onChange={(e) => setForm({ ...form, field_name: e.target.value })}
                  placeholder="e.g. status or leave blank for DocType"
                />
              </div>
              <div>
                <Label>Property</Label>
                <Input
                  value={form.property}
                  onChange={(e) => setForm({ ...form, property: e.target.value })}
                  placeholder="e.g. hidden, read_only, label"
                />
              </div>
              <div>
                <Label>Value</Label>
                <Input
                  value={form.value}
                  onChange={(e) => setForm({ ...form, value: e.target.value })}
                  placeholder="Property value"
                />
              </div>
              <div>
                <Label>Property Type</Label>
                <select
                  value={form.property_type}
                  onChange={(e) => setForm({ ...form, property_type: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="Data">Data</option>
                  <option value="Check">Check</option>
                  <option value="Select">Select</option>
                  <option value="Int">Int</option>
                  <option value="Text">Text</option>
                </select>
              </div>
            </div>
            <Button
              onClick={() => saveMutation.mutate()}
              disabled={!form.property || saveMutation.isPending}
            >
              <Save className="mr-2 size-4" />
              {saveMutation.isPending ? 'Saving...' : 'Set Property'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Setters Table */}
      {isLoading ? (
        <Skeleton className="h-48" />
      ) : !data || data.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          No property setters for this DocType
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Property</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Type</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((ps: any) => (
                  <TableRow key={ps.name}>
                    <TableCell>
                      <code className="text-xs bg-muted px-1 py-0.5 rounded">
                        {ps.field_name || '(DocType)'}
                      </code>
                    </TableCell>
                    <TableCell className="font-medium">{ps.property}</TableCell>
                    <TableCell className="max-w-48 truncate">{ps.value}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{ps.property_type}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────
export function SchemaManager() {
  const [selectedDoctype, setSelectedDoctype] = useState('');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Database className="size-8 text-primary" />
          Schema Manager
        </h1>
        <p className="mt-2 text-muted-foreground">
          Add Custom Fields and Property Setters to any DocType
        </p>
      </div>

      {/* DocType Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Select DocType</CardTitle>
        </CardHeader>
        <CardContent>
          <DocTypeSearch value={selectedDoctype} onChange={setSelectedDoctype} />
          {selectedDoctype && (
            <Badge className="mt-2" variant="default">{selectedDoctype}</Badge>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="fields">
        <TabsList>
          <TabsTrigger value="fields" className="flex items-center gap-2">
            <Columns3 className="size-4" /> Custom Fields
          </TabsTrigger>
          <TabsTrigger value="setters" className="flex items-center gap-2">
            <Settings2 className="size-4" /> Property Setters
          </TabsTrigger>
        </TabsList>

        <TabsContent value="fields" className="mt-4">
          <CustomFieldsTab doctype={selectedDoctype} />
        </TabsContent>

        <TabsContent value="setters" className="mt-4">
          <PropertySettersTab doctype={selectedDoctype} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
