/**
 * ExcelPreview — Shows a preview of a parsed Excel/CSV file
 * Displays columns, row count, and a preview table of the first rows.
 */
import { FileSpreadsheet, Columns3, Rows3 } from 'lucide-react';

export function ExcelPreview({ result }: { result: any }) {
  const columns = result.columns || [];
  const preview = result.preview || [];
  const totalRows = result.total_rows || 0;
  const format = result.format || 'excel';
  const sheet = result.sheet || '';

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      {/* Header */}
      <div className="bg-emerald-500/5 px-4 py-2.5 border-b border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="size-4 text-emerald-600" />
          <span className="text-xs font-semibold text-foreground">
            {format === 'csv' ? 'CSV' : 'Excel'} File Parsed
          </span>
          {sheet && (
            <span className="text-[10px] text-muted-foreground">· Sheet: {sheet}</span>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-6 px-4 py-3 bg-muted/10 border-b border-border/20">
        <div className="flex items-center gap-2">
          <Columns3 className="size-3.5 text-muted-foreground" />
          <span className="text-xs">
            <span className="font-semibold">{columns.length}</span>
            <span className="text-muted-foreground ml-1">columns</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Rows3 className="size-3.5 text-muted-foreground" />
          <span className="text-xs">
            <span className="font-semibold">{totalRows.toLocaleString()}</span>
            <span className="text-muted-foreground ml-1">rows</span>
          </span>
        </div>
      </div>

      {/* Column list */}
      <div className="px-4 py-2.5 border-b border-border/20">
        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">Columns</p>
        <div className="flex flex-wrap gap-1.5">
          {columns.map((col: string) => (
            <span
              key={col}
              className="inline-block rounded-md border border-border/50 bg-background px-2 py-0.5 text-[11px] font-medium"
            >
              {col}
            </span>
          ))}
        </div>
      </div>

      {/* Preview table */}
      {preview.length > 0 && (
        <>
          <div className="px-4 py-2 bg-muted/10 border-b border-border/20">
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
              Preview (first {preview.length} rows)
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/30 bg-muted/10">
                  {columns.slice(0, 6).map((col: string) => (
                    <th key={col} className="px-3 py-1.5 text-left text-[10px] font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                  {columns.length > 6 && (
                    <th className="px-3 py-1.5 text-[10px] text-muted-foreground">+{columns.length - 6} more</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {preview.map((row: any, i: number) => (
                  <tr key={i} className="border-b border-border/10 last:border-0">
                    {columns.slice(0, 6).map((col: string) => (
                      <td key={col} className="px-3 py-1.5 max-w-[160px] truncate text-foreground whitespace-nowrap">
                        {row[col] ?? '—'}
                      </td>
                    ))}
                    {columns.length > 6 && <td className="px-3 py-1.5 text-muted-foreground">…</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
