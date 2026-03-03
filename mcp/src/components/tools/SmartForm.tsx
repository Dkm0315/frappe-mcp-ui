/**
 * SmartForm Component
 * Intelligent form that adapts to DocType schema - NO JSON REQUIRED
 *
 * Uses custom autocomplete dropdown instead of cmdk to avoid
 * React 19 infinite loop (Radix Presence setNode -> setState loop).
 */
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { FormField, LinkFieldOption } from '@/types';

// ── Link Field Autocomplete (replaces cmdk Command) ────────────────
function LinkFieldAutocomplete({
  value,
  onChange,
  linkDoctype,
  placeholder,
}: {
  value: string;
  onChange: (val: string) => void;
  linkDoctype: string;
  placeholder: string;
}) {
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const { data: options, isLoading } = useQuery({
    queryKey: ['link-autocomplete', linkDoctype, search],
    queryFn: async () => {
      if (!linkDoctype) return [];
      const results = await api.searchLinkField(linkDoctype, search || '', 20);
      return results as LinkFieldOption[];
    },
    enabled: isOpen && !!linkDoctype,
  });

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="pl-9"
        />
      </div>
      {value && (
        <div className="mt-1.5 flex items-center gap-2">
          <Badge variant="secondary">{value}</Badge>
          <button
            type="button"
            onClick={() => { onChange(''); setSearch(''); }}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear
          </button>
        </div>
      )}
      {isOpen && (
        <>
          {/* Backdrop to close on click outside */}
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md max-h-60 overflow-y-auto">
            {isLoading && (
              <div className="p-3 text-center text-sm text-muted-foreground">
                Searching...
              </div>
            )}
            {!isLoading && options && options.length === 0 && search && (
              <div className="p-3 text-center text-sm text-muted-foreground">
                No results found for &ldquo;{search}&rdquo;
              </div>
            )}
            {!isLoading && options && options.length === 0 && !search && (
              <div className="p-3 text-center text-sm text-muted-foreground">
                Type to search {linkDoctype}...
              </div>
            )}
            {options?.map((opt) => (
              <button
                key={opt.value}
                type="button"
                className={cn(
                  'flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors text-left',
                  value === opt.value && 'bg-accent/50 font-medium'
                )}
                onClick={() => {
                  onChange(opt.value);
                  setSearch('');
                  setIsOpen(false);
                }}
              >
                <div className="flex flex-col">
                  <span>{opt.label}</span>
                  {opt.description && (
                    <span className="text-xs text-muted-foreground">{opt.description}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ── SmartForm ───────────────────────────────────────────────────────
interface SmartFormProps {
  doctype: string;
  initialValues?: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
}

export function SmartForm({ doctype, initialValues = {}, onChange }: SmartFormProps) {
  const [formValues, setFormValues] = useState<Record<string, any>>(initialValues);

  const { data: schema, isLoading } = useQuery({
    queryKey: ['form-schema', doctype],
    queryFn: async () => {
      const response = await api.getDocTypeFormFields(doctype);
      return response;
    },
  });

  useEffect(() => {
    onChange(formValues);
  }, [formValues]);

  const handleFieldChange = (fieldname: string, value: any) => {
    setFormValues(prev => ({ ...prev, [fieldname]: value }));
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (!schema?.fields || schema.fields.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center">
        <p className="text-sm text-muted-foreground">
          No editable fields found for {doctype}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        {schema.fields.map((field) => (
          <FormFieldRenderer
            key={field.fieldname}
            field={field}
            value={formValues[field.fieldname]}
            onChange={(value) => handleFieldChange(field.fieldname, value)}
          />
        ))}
      </div>
    </div>
  );
}

// ── Form Field Renderer ─────────────────────────────────────────────
interface FormFieldRendererProps {
  field: FormField;
  value: any;
  onChange: (value: any) => void;
}

function FormFieldRenderer({ field, value, onChange }: FormFieldRendererProps) {
  const fullWidth = field.input_type === 'textarea' || field.input_type === 'richtext';

  return (
    <div className={cn('space-y-2', fullWidth && 'md:col-span-2')}>
      <Label htmlFor={field.fieldname}>
        {field.label}
        {field.required && <span className="ml-1 text-red-600">*</span>}
      </Label>

      {field.input_type === 'text' && (
        <Input
          id={field.fieldname}
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.description || `Enter ${field.label.toLowerCase()}`}
        />
      )}

      {field.input_type === 'number' && (
        <Input
          id={field.fieldname}
          type="number"
          step={field.number_type === 'decimal' ? '0.01' : '1'}
          value={value || ''}
          onChange={(e) => onChange(field.number_type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value))}
          placeholder={field.description || `Enter ${field.label.toLowerCase()}`}
        />
      )}

      {field.input_type === 'select' && (
        <Select value={value || ''} onValueChange={onChange}>
          <SelectTrigger>
            <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
          </SelectTrigger>
          <SelectContent>
            {field.options?.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {field.input_type === 'checkbox' && (
        <div className="flex items-center space-x-2">
          <Checkbox
            id={field.fieldname}
            checked={!!value}
            onCheckedChange={onChange}
          />
          <label htmlFor={field.fieldname} className="text-sm text-muted-foreground">
            {field.description || field.label}
          </label>
        </div>
      )}

      {field.input_type === 'date' && (
        <Input
          id={field.fieldname}
          type="date"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      {field.input_type === 'datetime' && (
        <Input
          id={field.fieldname}
          type="datetime-local"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      {field.input_type === 'time' && (
        <Input
          id={field.fieldname}
          type="time"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
        />
      )}

      {field.input_type === 'textarea' && (
        <Textarea
          id={field.fieldname}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.description || `Enter ${field.label.toLowerCase()}`}
          rows={4}
        />
      )}

      {field.input_type === 'richtext' && (
        <Textarea
          id={field.fieldname}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.description || `Enter ${field.label.toLowerCase()}`}
          rows={6}
        />
      )}

      {field.input_type === 'autocomplete' && (
        <LinkFieldAutocomplete
          value={value || ''}
          onChange={onChange}
          linkDoctype={field.link_doctype || ''}
          placeholder={`Search ${field.link_doctype || field.label}...`}
        />
      )}

      {field.description && field.input_type !== 'checkbox' && field.input_type !== 'autocomplete' && (
        <p className="text-xs text-muted-foreground">{field.description}</p>
      )}
    </div>
  );
}
