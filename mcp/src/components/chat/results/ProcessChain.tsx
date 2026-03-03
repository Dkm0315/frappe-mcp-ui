/**
 * ProcessChain — Visual chain showing document mapping (SO → DN → SI)
 */
import { ArrowRight, CheckCircle2, ExternalLink } from 'lucide-react';

export function ProcessChain({ result, toolName }: { result: any; toolName: string }) {
  if (toolName === 'make_mapped_document') {
    const source = result.source || {};
    const target = result.target || {};

    return (
      <div className="rounded-xl border border-border/50 bg-muted/10 p-4">
        <p className="text-[11px] text-muted-foreground mb-3 font-medium">Document Chain</p>
        <div className="flex items-center gap-3">
          <DocBadge doctype={source.doctype} name={source.name} status="completed" />
          <ArrowRight className="size-4 text-primary shrink-0" />
          <DocBadge doctype={target.doctype} name={target.name} status="created" />
        </div>
      </div>
    );
  }

  // get_linked_documents
  const linked = result.linked_documents || {};
  const entries = Object.entries(linked);

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        No linked documents found.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border/50 overflow-hidden">
      <div className="bg-muted/30 px-3 py-2 border-b border-border/30">
        <span className="text-[11px] font-medium text-muted-foreground">
          Linked Documents for {result.doctype} — {result.name}
        </span>
      </div>
      <div className="divide-y divide-border/20">
        {entries.map(([dt, docs]: [string, any]) => (
          <div key={dt} className="px-3 py-2">
            <p className="text-[11px] font-medium text-muted-foreground mb-1">{dt}</p>
            <div className="flex flex-wrap gap-1.5">
              {(docs as any[]).map((doc: any) => (
                <a
                  key={doc.name}
                  href={`/app/${dt.toLowerCase().replace(/ /g, '-')}/${doc.name}`}
                  target="_blank"
                  rel="noopener"
                  className="inline-flex items-center gap-1 rounded-md border border-border/50 bg-background px-2 py-1 text-[10px] hover:border-primary/30 transition-colors"
                >
                  {doc.name}
                  {doc.status && <span className="text-muted-foreground">({doc.status})</span>}
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DocBadge({ doctype, name, status }: { doctype: string; name: string; status: string }) {
  const frappeUrl = `/app/${(doctype || '').toLowerCase().replace(/ /g, '-')}/${name}`;

  return (
    <a
      href={frappeUrl}
      target="_blank"
      rel="noopener"
      className="flex items-center gap-2 rounded-lg border border-border/50 bg-background px-3 py-2 hover:border-primary/30 transition-colors"
    >
      {status === 'completed' && <CheckCircle2 className="size-3.5 text-emerald-500" />}
      {status === 'created' && <CheckCircle2 className="size-3.5 text-blue-500" />}
      <div>
        <p className="text-[10px] text-muted-foreground">{doctype}</p>
        <p className="text-xs font-medium">{name}</p>
      </div>
      <ExternalLink className="size-3 text-muted-foreground/50" />
    </a>
  );
}
