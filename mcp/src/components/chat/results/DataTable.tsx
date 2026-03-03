/**
 * DataTable — Renders tabular data from get_list, run_report, analyze_data
 */
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';

interface DataTableProps {
  result: any;
  toolName: string;
}

export function DataTable({ result, toolName }: DataTableProps) {
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [expanded, setExpanded] = useState(false);

  const data = result.data || result.result || [];
  const rows = Array.isArray(data) ? data : [];
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        No records found.
      </div>
    );
  }

  // Get columns from first row
  const allColumns = Object.keys(rows[0]).filter(k => !k.startsWith('_'));
  const columns = allColumns.slice(0, 6); // Show max 6 columns

  // Sort
  const sortedRows = [...rows];
  if (sortField) {
    sortedRows.sort((a, b) => {
      const av = a[sortField], bv = b[sortField];
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }

  const displayRows = expanded ? sortedRows : sortedRows.slice(0, 10);

  const handleSort = (col: string) => {
    if (sortField === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(col);
      setSortDir('asc');
    }
  };

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between bg-muted/30 px-3 py-2 border-b border-border/30">
        <span className="text-[11px] font-medium text-muted-foreground">
          {result.doctype || result.report || 'Results'} — {rows.length} record{rows.length !== 1 ? 's' : ''}
          {result.truncated && ' (truncated)'}
        </span>
        {result.file_url && (
          <a href={result.file_url} download className="flex items-center gap-1 text-[10px] text-primary hover:underline">
            <Download className="size-3" /> Download
          </a>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border/30 bg-muted/10">
              {columns.map(col => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  className="px-3 py-2 text-left font-medium text-muted-foreground cursor-pointer hover:text-foreground select-none"
                >
                  <span className="flex items-center gap-1">
                    {formatColumnName(col)}
                    {sortField === col && (sortDir === 'asc' ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, i) => (
              <tr key={i} className="border-b border-border/20 last:border-0 hover:bg-muted/20">
                {columns.map(col => (
                  <td key={col} className="px-3 py-2 max-w-[200px] truncate">
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show more */}
      {rows.length > 10 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full py-2 text-[11px] text-primary hover:bg-muted/30 border-t border-border/30 transition-colors"
        >
          {expanded ? 'Show less' : `Show all ${rows.length} rows`}
        </button>
      )}
    </div>
  );
}

function formatColumnName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatValue(val: any): string {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}
