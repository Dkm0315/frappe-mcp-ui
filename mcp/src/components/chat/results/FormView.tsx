/**
 * FormView — Renders a Frappe document as a proper form with labeled fields
 *
 * Instead of JSON dumps, displays fields in a clean form layout:
 * - Labels above values (like a read-only form)
 * - Status badges with colors
 * - Currency/number formatting
 * - Date formatting
 * - Link fields as clickable links
 * - Child tables as mini tables
 * - Internal/system fields hidden
 */
import { useState } from 'react';
import { ExternalLink, ChevronDown, FileText, Hash, Calendar, DollarSign, Link2, Type, ToggleLeft, Table2 } from 'lucide-react';
import { cn } from '@/lib/utils';

// Fields to always hide from form view
const HIDDEN_FIELDS = new Set([
  'doctype', 'docstatus', 'owner', 'creation', 'modified', 'modified_by',
  'idx', '_liked_by', '_comments', '_assign', '_user_tags', '_seen',
  '__islocal', '__unsaved', '__last_sync_on', 'parent', 'parenttype',
  'parentfield', 'amended_from', '__onload',
]);

// Status color mapping
const STATUS_COLORS: Record<string, string> = {
  Draft: 'bg-slate-100 text-slate-700 border-slate-200',
  Open: 'bg-blue-50 text-blue-700 border-blue-200',
  Active: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Enabled: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Submitted: 'bg-blue-50 text-blue-700 border-blue-200',
  Approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Closed: 'bg-slate-100 text-slate-600 border-slate-200',
  Cancelled: 'bg-red-50 text-red-600 border-red-200',
  Overdue: 'bg-red-50 text-red-600 border-red-200',
  'On Hold': 'bg-amber-50 text-amber-700 border-amber-200',
  Pending: 'bg-amber-50 text-amber-700 border-amber-200',
  'To Deliver and Bill': 'bg-amber-50 text-amber-700 border-amber-200',
  'To Bill': 'bg-amber-50 text-amber-700 border-amber-200',
  'To Deliver': 'bg-amber-50 text-amber-700 border-amber-200',
  Paid: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Unpaid: 'bg-red-50 text-red-600 border-red-200',
  'Partly Paid': 'bg-amber-50 text-amber-700 border-amber-200',
  'Return': 'bg-orange-50 text-orange-600 border-orange-200',
};

interface FormViewProps {
  data: Record<string, any>;
  doctype?: string;
  name?: string;
  /** Max fields to show before "Show more" */
  maxFields?: number;
  /** Show the "Open in Frappe" header */
  showHeader?: boolean;
  /** Compact mode — single-column, smaller text */
  compact?: boolean;
}

export function FormView({
  data,
  doctype,
  name,
  maxFields = 16,
  showHeader = true,
  compact = false,
}: FormViewProps) {
  const [expanded, setExpanded] = useState(false);

  const dt = doctype || data.doctype || '';
  const docName = name || data.name || '';
  const frappeUrl = dt && docName
    ? `/app/${dt.toLowerCase().replace(/ /g, '-')}/${docName}`
    : '';

  // Separate fields into categories
  const { mainFields, childTables } = categorizeFields(data);

  const visibleFields = expanded ? mainFields : mainFields.slice(0, maxFields);
  const hasMore = mainFields.length > maxFields;

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      {/* Header */}
      {showHeader && dt && (
        <div className="flex items-center justify-between bg-muted/30 px-4 py-2.5 border-b border-border/30">
          <div className="flex items-center gap-2">
            <FileText className="size-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold text-foreground">{dt}</span>
            <span className="text-xs text-muted-foreground">·</span>
            <span className="text-xs font-medium text-muted-foreground">{docName}</span>
          </div>
          {frappeUrl && (
            <a
              href={frappeUrl}
              target="_blank"
              rel="noopener"
              className="flex items-center gap-1.5 text-[11px] text-primary hover:text-primary/80 font-medium transition-colors"
            >
              Open <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      )}

      {/* Form fields — 2 column grid */}
      <div className={cn(
        'grid gap-x-6 gap-y-0.5 p-4',
        compact ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2',
      )}>
        {visibleFields.map(({ key, value, type }) => (
          <FormField
            key={key}
            label={formatLabel(key)}
            value={value}
            fieldType={type}
            compact={compact}
            doctype={dt}
          />
        ))}
      </div>

      {/* Show more toggle */}
      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-center gap-1.5 w-full py-2 text-[11px] text-primary hover:bg-muted/20 border-t border-border/30 transition-colors font-medium"
        >
          {expanded ? 'Show less' : `Show all ${mainFields.length} fields`}
          <ChevronDown className={cn('size-3 transition-transform', expanded && 'rotate-180')} />
        </button>
      )}

      {/* Child tables */}
      {childTables.map(({ key, rows }) => (
        <ChildTable key={key} label={formatLabel(key)} rows={rows} />
      ))}
    </div>
  );
}

// ── Field Renderer ──────────────────────────────────────────────────

type FieldType = 'status' | 'currency' | 'number' | 'date' | 'link' | 'check' | 'text' | 'longtext' | 'html';

function FormField({
  label,
  value,
  fieldType,
  compact,
  doctype,
}: {
  label: string;
  value: any;
  fieldType: FieldType;
  compact?: boolean;
  doctype?: string;
}) {
  const isEmpty = value === null || value === undefined || value === '';

  return (
    <div className={cn('py-2 border-b border-border/10 last:border-0', compact && 'py-1.5')}>
      <div className="flex items-center gap-1.5 mb-0.5">
        <FieldIcon type={fieldType} />
        <span className={cn(
          'text-muted-foreground font-medium uppercase tracking-wider',
          compact ? 'text-[9px]' : 'text-[10px]',
        )}>
          {label}
        </span>
      </div>
      <div className={cn('pl-5', compact ? 'text-xs' : 'text-sm')}>
        {isEmpty ? (
          <span className="text-muted-foreground/40 italic text-xs">—</span>
        ) : fieldType === 'status' ? (
          <StatusBadge status={String(value)} />
        ) : fieldType === 'currency' ? (
          <span className="font-semibold tabular-nums">{formatCurrency(value)}</span>
        ) : fieldType === 'number' ? (
          <span className="font-medium tabular-nums">{formatNumber(value)}</span>
        ) : fieldType === 'date' ? (
          <span className="text-foreground">{formatDate(value)}</span>
        ) : fieldType === 'check' ? (
          <span className={cn(
            'inline-flex items-center gap-1 text-xs font-medium',
            value ? 'text-emerald-600' : 'text-muted-foreground',
          )}>
            {value ? 'Yes' : 'No'}
          </span>
        ) : fieldType === 'link' ? (
          <LinkValue value={String(value)} />
        ) : fieldType === 'longtext' ? (
          <p className="text-foreground whitespace-pre-wrap line-clamp-3">{String(value)}</p>
        ) : (
          <span className="text-foreground">{String(value)}</span>
        )}
      </div>
    </div>
  );
}

function FieldIcon({ type }: { type: FieldType }) {
  const cls = 'size-3 text-muted-foreground/40';
  switch (type) {
    case 'currency': return <DollarSign className={cls} />;
    case 'number': return <Hash className={cls} />;
    case 'date': return <Calendar className={cls} />;
    case 'link': return <Link2 className={cls} />;
    case 'check': return <ToggleLeft className={cls} />;
    case 'status': return <ToggleLeft className={cls} />;
    default: return <Type className={cls} />;
  }
}

function StatusBadge({ status }: { status: string }) {
  const colors = STATUS_COLORS[status] || 'bg-muted text-muted-foreground border-border/50';
  return (
    <span className={cn('inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-semibold', colors)}>
      {status}
    </span>
  );
}

function LinkValue({ value }: { value: string }) {
  // If it looks like a doc name (e.g., SO-00145, ITEM-001), make it clickable
  if (/^[A-Z]/.test(value) && !value.includes(' ')) {
    return (
      <span className="text-primary font-medium cursor-default">{value}</span>
    );
  }
  return <span className="text-foreground">{value}</span>;
}

// ── Child Table ──────────────────────────────────────────────────────

function ChildTable({ label, rows }: { label: string; rows: any[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!rows.length) return null;

  // Get visible columns (skip internal fields)
  const allCols = Object.keys(rows[0]).filter(k =>
    !HIDDEN_FIELDS.has(k) && !k.startsWith('_') && k !== 'name'
  );
  const columns = allCols.slice(0, 6);
  const displayRows = expanded ? rows : rows.slice(0, 5);

  return (
    <div className="border-t border-border/30">
      <div className="flex items-center gap-2 px-4 py-2 bg-muted/20">
        <Table2 className="size-3 text-muted-foreground" />
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{label}</span>
        <span className="text-[10px] text-muted-foreground">({rows.length})</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border/30 bg-muted/10">
              {columns.map(col => (
                <th key={col} className="px-3 py-1.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  {formatLabel(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, i) => (
              <tr key={i} className="border-b border-border/10 last:border-0">
                {columns.map(col => (
                  <td key={col} className="px-3 py-1.5 max-w-[180px] truncate text-foreground">
                    {formatSimpleValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-center gap-1 w-full py-1.5 text-[10px] text-primary hover:bg-muted/20 border-t border-border/20 transition-colors"
        >
          {expanded ? 'Show less' : `Show all ${rows.length} rows`}
          <ChevronDown className={cn('size-2.5 transition-transform', expanded && 'rotate-180')} />
        </button>
      )}
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────

function categorizeFields(data: Record<string, any>) {
  const mainFields: { key: string; value: any; type: FieldType }[] = [];
  const childTables: { key: string; rows: any[] }[] = [];

  // Put status first
  const entries = Object.entries(data);
  const sorted = entries.sort(([a], [b]) => {
    if (a === 'status' || a === 'workflow_state') return -1;
    if (b === 'status' || b === 'workflow_state') return 1;
    if (a === 'name') return -1;
    if (b === 'name') return 1;
    return 0;
  });

  for (const [key, value] of sorted) {
    // Skip hidden fields
    if (HIDDEN_FIELDS.has(key) || key.startsWith('_')) continue;

    // Child table (array of objects)
    if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'object') {
      childTables.push({ key, rows: value });
      continue;
    }

    // Skip arrays/objects that aren't child tables
    if (Array.isArray(value) || (typeof value === 'object' && value !== null)) continue;

    const type = detectFieldType(key, value);
    mainFields.push({ key, value, type });
  }

  return { mainFields, childTables };
}

function detectFieldType(key: string, value: any): FieldType {
  const k = key.toLowerCase();

  // Status fields
  if (k === 'status' || k === 'workflow_state' || k === 'docstatus') return 'status';

  // Currency fields
  if (k.includes('amount') || k.includes('total') || k.includes('rate') ||
      k.includes('price') || k.includes('cost') || k.includes('tax') ||
      k.includes('grand_total') || k.includes('net_total') ||
      k.includes('base_') || k.includes('_amount')) return 'currency';

  // Number fields
  if (k.includes('qty') || k.includes('quantity') || k.includes('count') ||
      k.includes('_no') || k.includes('percent') || k === 'per_delivered' ||
      k === 'per_billed' || k === 'per_returned') return 'number';

  // Date fields
  if (k.includes('date') || k === 'valid_till' || k === 'due_date' ||
      k === 'posting_date' || k === 'transaction_date' || k === 'delivery_date') return 'date';

  // Check/boolean fields
  if (typeof value === 'boolean' || (typeof value === 'number' && (value === 0 || value === 1) &&
      (k.startsWith('is_') || k.startsWith('has_') || k.startsWith('enable_') ||
       k.startsWith('disable_') || k.startsWith('allow_')))) return 'check';

  // Link fields (IDs that reference other docs)
  if (typeof value === 'string' && value && !value.includes(' ') &&
      (k.includes('_id') || k === 'customer' || k === 'supplier' || k === 'company' ||
       k === 'warehouse' || k === 'cost_center' || k === 'project' || k === 'territory' ||
       k === 'customer_group' || k === 'item_code' || k === 'item_group' ||
       k === 'sales_order' || k === 'purchase_order' || k === 'delivery_note' ||
       k === 'sales_invoice' || k === 'purchase_invoice' || k === 'material_request' ||
       k === 'assigned_to' || k === 'lead')) return 'link';

  // Long text
  if (typeof value === 'string' && value.length > 200) return 'longtext';

  // Date-like strings
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) return 'date';

  return 'text';
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
    .replace(/\bId\b/g, 'ID')
    .replace(/\bUrl\b/g, 'URL');
}

function formatCurrency(val: any): string {
  const num = Number(val);
  if (isNaN(num)) return String(val);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(num);
}

function formatNumber(val: any): string {
  const num = Number(val);
  if (isNaN(num)) return String(val);
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(num);
}

function formatDate(val: any): string {
  if (!val) return '—';
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return String(val);
    // Check if it's just a date (no time component)
    const str = String(val);
    if (str.length <= 10) {
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    }
    return d.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return String(val);
  }
}

function formatSimpleValue(val: any): string {
  if (val === null || val === undefined || val === '') return '—';
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (typeof val === 'number') return val.toLocaleString('en-IN');
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}
