/**
 * WorkflowInfo — Visual workflow states and pending approvals
 */
import { cn } from '@/lib/utils';
import { Circle, CheckCircle2, Clock, ExternalLink } from 'lucide-react';

export function WorkflowInfo({ result, toolName }: { result: any; toolName: string }) {
  if (toolName === 'get_pending_approvals') {
    const pending = result.pending_approvals || [];

    if (pending.length === 0) {
      return (
        <div className="flex items-center gap-2 rounded-xl border border-border/50 bg-emerald-500/5 px-4 py-3 text-sm">
          <CheckCircle2 className="size-4 text-emerald-500" />
          <span>No pending approvals — you're all caught up!</span>
        </div>
      );
    }

    return (
      <div className="rounded-xl border border-border/50 overflow-hidden">
        <div className="bg-amber-500/5 px-3 py-2 border-b border-border/30">
          <span className="text-[11px] font-medium text-amber-600">
            {pending.length} pending approval{pending.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="divide-y divide-border/20">
          {pending.map((doc: any, i: number) => {
            const frappeUrl = `/app/${(doc.doctype || '').toLowerCase().replace(/ /g, '-')}/${doc.name}`;
            return (
              <a
                key={i}
                href={frappeUrl}
                target="_blank"
                rel="noopener"
                className="flex items-center gap-3 px-3 py-2.5 hover:bg-muted/20 transition-colors"
              >
                <Clock className="size-3.5 text-amber-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{doc.doctype}: {doc.name}</p>
                  <p className="text-[10px] text-muted-foreground">{doc.workflow_state}</p>
                </div>
                <ExternalLink className="size-3 text-muted-foreground/40 shrink-0" />
              </a>
            );
          })}
        </div>
      </div>
    );
  }

  // Workflow info
  if (!result.has_workflow) {
    return (
      <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        {result.message || 'No workflow configured.'}
      </div>
    );
  }

  const states = result.states || [];
  const currentState = result.current_state;

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      <div className="bg-muted/30 px-3 py-2 border-b border-border/30">
        <span className="text-[11px] font-medium text-muted-foreground">
          Workflow: {result.workflow_name}
        </span>
      </div>
      <div className="px-4 py-3">
        <div className="flex items-center gap-2 flex-wrap">
          {states.map((s: any, i: number) => {
            const isCurrent = s.state === currentState;
            return (
              <div key={i} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-muted-foreground/30">→</span>}
                <div className={cn(
                  'flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium border',
                  isCurrent
                    ? 'bg-primary/10 text-primary border-primary/30'
                    : 'bg-muted/30 text-muted-foreground border-border/30'
                )}>
                  {isCurrent ? <Circle className="size-2 fill-primary text-primary" /> : <Circle className="size-2 text-muted-foreground/30" />}
                  {s.state}
                </div>
              </div>
            );
          })}
        </div>
        {result.available_actions?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/20">
            <p className="text-[10px] text-muted-foreground mb-1.5">Available actions:</p>
            <div className="flex gap-1.5 flex-wrap">
              {result.available_actions.map((a: any, i: number) => (
                <span key={i} className="rounded-md bg-primary/10 text-primary px-2 py-0.5 text-[10px] font-medium">
                  {a.action} → {a.next_state}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
