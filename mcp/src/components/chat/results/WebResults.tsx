/**
 * WebResults — Search results from the web (DuckDuckGo)
 */
import { Globe, ExternalLink } from 'lucide-react';

export function WebResults({ result }: { result: any }) {
  const results = result.results || [];

  if (results.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        <Globe className="size-4" />
        No web results found.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {results.map((r: any, i: number) => (
        <a
          key={i}
          href={r.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex gap-3 rounded-xl border border-border/50 bg-muted/10 p-3 hover:border-primary/20 hover:bg-muted/20 transition-all"
        >
          <Globe className="size-4 text-primary/50 shrink-0 mt-0.5" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-primary truncate">{r.title}</p>
            <p className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5">{r.body}</p>
            <p className="text-[10px] text-muted-foreground/50 truncate mt-1">{r.url}</p>
          </div>
          <ExternalLink className="size-3 text-muted-foreground/30 shrink-0 mt-0.5" />
        </a>
      ))}
    </div>
  );
}
