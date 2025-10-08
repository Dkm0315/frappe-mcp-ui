/**
 * SmartForm Component
 * Intelligent form that adapts to DocType schema - NO JSON REQUIRED
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
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Check, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { FormField, LinkFieldOption } from '@/types';

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

interface FormFieldRendererProps {
  field: FormField;
  value: any;
  onChange: (value: any) => void;
}

function FormFieldRenderer({ field, value, onChange }: FormFieldRendererProps) {
  const [linkSearch, setLinkSearch] = useState('');
  const [linkOpen, setLinkOpen] = useState(false);

  const { data: linkOptions } = useQuery({
    queryKey: ['link-options', field.link_doctype, linkSearch],
    queryFn: async () => {
      if (!field.link_doctype || !linkSearch) return [];
      const options = await api.searchLinkField(field.link_doctype, linkSearch);
      return options as LinkFieldOption[];
    },
    enabled: field.input_type === 'autocomplete' && !!linkSearch,
  });

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

      {field.input_type === 'autocomplete' && (
        <Popover open={linkOpen} onOpenChange={setLinkOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={linkOpen}
              className="w-full justify-between"
            >
              {value || `Select ${field.label.toLowerCase()}...`}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-full p-0">
            <Command>
              <CommandInput
                placeholder={`Search ${field.link_doctype}...`}
                value={linkSearch}
                onValueChange={setLinkSearch}
              />
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup>
                {linkOptions?.map((option) => (
                  <CommandItem
                    key={option.value}
                    value={option.value}
                    onSelect={() => {
                      onChange(option.value);
                      setLinkOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        'mr-2 h-4 w-4',
                        value === option.value ? 'opacity-100' : 'opacity-0'
                      )}
                    />
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      {option.description && (
                        <span className="text-xs text-muted-foreground">
                          {option.description}
                        </span>
                      )}
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            </Command>
          </PopoverContent>
        </Popover>
      )}

      {field.description && field.input_type !== 'checkbox' && (
        <p className="text-xs text-muted-foreground">{field.description}</p>
      )}
    </div>
  );
}

