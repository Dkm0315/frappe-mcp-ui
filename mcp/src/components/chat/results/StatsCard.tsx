/**
 * StatsCard — Number cards for get_count, get_dashboard_data
 */
export function StatsCard({ result, toolName }: { result: any; toolName: string }) {
  if (toolName === 'get_count') {
    return (
      <div className="inline-flex items-center gap-3 rounded-xl border border-border/50 bg-muted/10 px-4 py-3">
        <div className="text-2xl font-bold text-primary tabular-nums">{result.count?.toLocaleString()}</div>
        <div className="text-xs text-muted-foreground">{result.doctype}</div>
      </div>
    );
  }

  // Dashboard data
  const breakdown = result.status_breakdown || {};
  const entries = Object.entries(breakdown);

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      <div className="bg-muted/30 px-3 py-2 border-b border-border/30 flex items-center justify-between">
        <span className="text-[11px] font-medium text-muted-foreground">{result.doctype} Dashboard</span>
        <span className="text-sm font-bold tabular-nums">{result.total_count?.toLocaleString()} total</span>
      </div>
      {entries.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-px bg-border/20">
          {entries.map(([status, count]: [string, any]) => (
            <div key={status} className="bg-background px-3 py-2.5 text-center">
              <p className="text-lg font-bold tabular-nums">{Number(count).toLocaleString()}</p>
              <p className="text-[10px] text-muted-foreground">{status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
