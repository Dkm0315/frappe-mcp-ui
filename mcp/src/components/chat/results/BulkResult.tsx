/**
 * BulkResult — Progress bar + success/fail counts for bulk operations
 */
import { useState } from 'react';
import { CheckCircle2, XCircle, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export function BulkResult({ result, toolName }: { result: any; toolName: string }) {
  const [showErrors, setShowErrors] = useState(false);

  const created = result.created_count || 0;
  const updated = result.updated_count || 0;
  const deleted = result.deleted_count || 0;
  const failed = result.failed_count || 0;
  const total = (created || updated || deleted) + failed;
  const successCount = created || updated || deleted;
  const successPct = total > 0 ? (successCount / total) * 100 : 0;
  const errors = result.errors || [];

  const actionLabel = toolName.includes('create') || toolName.includes('import') ? 'created'
    : toolName.includes('update') ? 'updated'
    : 'deleted';

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      <div className="px-4 py-3 space-y-3">
        {/* Progress bar */}
        <div className="h-2 rounded-full bg-muted overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all', failed > 0 ? 'bg-amber-500' : 'bg-emerald-500')}
            style={{ width: `${successPct}%` }}
          />
        </div>

        {/* Counts */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="size-3.5 text-emerald-500" />
            <span className="text-sm font-medium">{successCount} {actionLabel}</span>
          </div>
          {failed > 0 && (
            <div className="flex items-center gap-1.5">
              <XCircle className="size-3.5 text-red-500" />
              <span className="text-sm font-medium text-red-600">{failed} failed</span>
            </div>
          )}
        </div>
      </div>

      {/* Errors expandable */}
      {errors.length > 0 && (
        <div className="border-t border-border/30">
          <button
            onClick={() => setShowErrors(!showErrors)}
            className="flex items-center justify-between w-full px-4 py-2 text-[11px] text-muted-foreground hover:bg-muted/20 transition-colors"
          >
            <span>{errors.length} error{errors.length !== 1 ? 's' : ''}</span>
            <ChevronDown className={cn('size-3 transition-transform', showErrors && 'rotate-180')} />
          </button>
          {showErrors && (
            <div className="px-4 pb-3 space-y-1.5 max-h-48 overflow-y-auto">
              {errors.map((err: any, i: number) => (
                <div key={i} className="text-[10px] text-red-600 bg-red-500/5 rounded-md px-2 py-1.5">
                  <span className="font-medium">Row {err.row || err.index || i + 1}:</span> {err.error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
