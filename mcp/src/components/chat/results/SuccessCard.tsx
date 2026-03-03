/**
 * SuccessCard — Shows success for create/update/submit/cancel/amend
 * Displays a success banner + the document in form view
 */
import { useState } from 'react';
import { CheckCircle2, ExternalLink, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FormView } from './FormView';

const actionLabels: Record<string, { label: string; color: string }> = {
  create_document: { label: 'Created', color: 'emerald' },
  update_document: { label: 'Updated', color: 'blue' },
  submit_document: { label: 'Submitted', color: 'emerald' },
  cancel_document: { label: 'Cancelled', color: 'amber' },
  amend_document: { label: 'Amended', color: 'blue' },
};

export function SuccessCard({ result, toolName }: { result: any; toolName: string }) {
  const [showDetails, setShowDetails] = useState(false);

  const action = actionLabels[toolName] || { label: 'Done', color: 'emerald' };
  const doctype = result.doctype || '';
  const name = result.name || result.amended_name || '';
  const frappeUrl = `/app/${doctype.toLowerCase().replace(/ /g, '-')}/${name}`;
  const hasData = result.data && Object.keys(result.data).length > 0;

  const colorMap: Record<string, string> = {
    emerald: 'border-emerald-500/20 bg-emerald-500/5',
    blue: 'border-blue-500/20 bg-blue-500/5',
    amber: 'border-amber-500/20 bg-amber-500/5',
  };
  const iconColorMap: Record<string, string> = {
    emerald: 'text-emerald-500',
    blue: 'text-blue-500',
    amber: 'text-amber-500',
  };

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      {/* Success banner */}
      <div className={cn('flex items-center gap-3 px-4 py-3', colorMap[action.color])}>
        <CheckCircle2 className={cn('size-5 shrink-0', iconColorMap[action.color])} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold">{action.label} {doctype}</p>
          <p className="text-xs text-muted-foreground truncate">{name}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {hasData && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
            >
              Details
              <ChevronDown className={cn('size-3 transition-transform', showDetails && 'rotate-180')} />
            </button>
          )}
          {name && (
            <a
              href={frappeUrl}
              target="_blank"
              rel="noopener"
              className="flex items-center gap-1 text-[11px] text-primary hover:text-primary/80 font-medium transition-colors"
            >
              Open <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      </div>

      {/* Document details (expandable form view) */}
      {showDetails && hasData && (
        <FormView
          data={result.data}
          doctype={doctype}
          name={name}
          maxFields={12}
          showHeader={false}
          compact
        />
      )}
    </div>
  );
}
