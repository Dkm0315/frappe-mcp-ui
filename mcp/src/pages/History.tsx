/**
 * History Page
 * View execution history with detailed logs
 */
import { CreditHistory } from '@/components/credits/CreditHistory';

export function History() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Execution History</h1>
        <p className="mt-2 text-muted-foreground">
          View your tool execution history and usage logs
        </p>
      </div>

      <CreditHistory />
    </div>
  );
}

