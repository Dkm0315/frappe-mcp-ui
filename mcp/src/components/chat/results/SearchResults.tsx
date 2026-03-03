/**
 * SearchResults — List of search matches with DocType badges
 */
import { ExternalLink, Search } from 'lucide-react';

export function SearchResults({ result }: { result: any }) {
  const docs = result.data || [];
  const doctype = result.doctype || '';

  if (docs.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        <Search className="size-4" />
        No results found.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      <div className="bg-muted/30 px-3 py-2 border-b border-border/30">
        <span className="text-[11px] font-medium text-muted-foreground">
          {docs.length} result{docs.length !== 1 ? 's' : ''} in {doctype}
        </span>
      </div>
      <div className="divide-y divide-border/20">
        {docs.slice(0, 20).map((doc: any) => {
          const frappeUrl = `/app/${doctype.toLowerCase().replace(/ /g, '-')}/${doc.name}`;
          return (
            <a
              key={doc.name}
              href={frappeUrl}
              target="_blank"
              rel="noopener"
              className="flex items-center gap-3 px-3 py-2 hover:bg-muted/20 transition-colors"
            >
              <span className="text-xs font-medium flex-1 truncate">{doc.name}</span>
              {Object.entries(doc)
                .filter(([k]) => k !== 'name')
                .slice(0, 2)
                .map(([k, v]) => (
                  <span key={k} className="text-[10px] text-muted-foreground truncate max-w-[120px]">
                    {String(v || '')}
                  </span>
                ))}
              <ExternalLink className="size-3 text-muted-foreground/40 shrink-0" />
            </a>
          );
        })}
      </div>
    </div>
  );
}
