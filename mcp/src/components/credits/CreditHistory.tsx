/**
 * CreditHistory Component
 * Timeline view of credit usage
 */
import { useUsageHistory } from '@/hooks/useCredits';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle2, XCircle, AlertCircle, Clock } from 'lucide-react';

export function CreditHistory() {
  const { data: logs, isLoading } = useUsageHistory();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Success':
        return <CheckCircle2 className="size-4 text-green-600" />;
      case 'Failed':
        return <XCircle className="size-4 text-red-600" />;
      case 'Partial':
        return <AlertCircle className="size-4 text-yellow-600" />;
      default:
        return <Clock className="size-4 text-blue-600" />;
    }
  };

  const getStatusVariant = (status: string): 'default' | 'secondary' | 'destructive' => {
    switch (status) {
      case 'Success':
        return 'default';
      case 'Failed':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!logs || logs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Usage History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-sm text-muted-foreground">No usage history yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage History</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="relative space-y-4">
            {/* Timeline line */}
            <div className="absolute left-4 top-2 bottom-2 w-px bg-border" />

            {logs.map((log) => (
              <div key={log.name} className="relative flex gap-4">
                {/* Status Icon */}
                <div className="relative z-10 flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-background bg-card">
                  {getStatusIcon(log.status)}
                </div>

                {/* Content */}
                <div className="flex-1 rounded-lg border bg-card p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{log.tool_name}</h4>
                        <Badge variant={getStatusVariant(log.status)} className="text-xs">
                          {log.status}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(log.creation), { addSuffix: true })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-sm font-semibold">
                        -{log.credits_consumed}
                      </p>
                      <p className="text-xs text-muted-foreground">credits</p>
                    </div>
                  </div>

                  {log.error_message && (
                    <p className="mt-2 text-xs text-red-600">{log.error_message}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

