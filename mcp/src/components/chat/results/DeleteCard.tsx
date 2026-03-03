/**
 * DeleteCard — Confirmation card for delete operations
 */
import { Trash2 } from 'lucide-react';

export function DeleteCard({ result }: { result: any }) {
  const message = result.message || 'Document deleted.';

  return (
    <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
      <Trash2 className="size-5 text-red-500 shrink-0" />
      <p className="text-sm font-medium text-red-700">{message}</p>
    </div>
  );
}
