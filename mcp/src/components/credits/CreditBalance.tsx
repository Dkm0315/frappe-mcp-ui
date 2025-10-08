/**
 * CreditBalance Component
 * Displays user's credit balance with color-coded states
 */
import { useCredits } from '@/hooks/useCredits';
import { useCreditStore } from '@/stores/creditStore';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Coins, TrendingDown, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface CreditBalanceProps {
  variant?: 'default' | 'compact';
}

export function CreditBalance({ variant = 'default' }: CreditBalanceProps) {
  const { data, isLoading } = useCredits();
  const { balance } = useCreditStore();

  const getBalanceColor = (bal: number) => {
    if (bal > 100) return 'text-green-600';
    if (bal > 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBalanceVariant = (bal: number): 'default' | 'secondary' | 'destructive' => {
    if (bal > 100) return 'default';
    if (bal > 50) return 'secondary';
    return 'destructive';
  };

  if (isLoading) {
    return variant === 'compact' ? (
      <Skeleton className="h-9 w-24" />
    ) : (
      <Card>
        <CardContent className="p-6">
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (variant === 'compact') {
    return (
      <Badge variant={getBalanceVariant(balance)} className="gap-1.5 px-3 py-1.5">
        <Coins className="size-3.5" />
        <motion.span
          key={balance}
          initial={{ scale: 1.2, color: '#10b981' }}
          animate={{ scale: 1, color: 'inherit' }}
          className="font-mono font-semibold"
        >
          {balance}
        </motion.span>
      </Badge>
    );
  }

  return (
    <Card className="border-2">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Credit Balance</p>
            <motion.p
              key={balance}
              initial={{ scale: 1.1 }}
              animate={{ scale: 1 }}
              className={cn('text-4xl font-bold tabular-nums', getBalanceColor(balance))}
            >
              {balance}
            </motion.p>
          </div>
          <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
            <Coins className="size-8 text-primary" />
          </div>
        </div>

        {data && (
          <div className="mt-4 grid grid-cols-2 gap-4 border-t pt-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="size-4 text-green-600" />
              <div>
                <p className="text-xs text-muted-foreground">Purchased</p>
                <p className="font-semibold tabular-nums">{data.total_purchased}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="size-4 text-red-600" />
              <div>
                <p className="text-xs text-muted-foreground">Consumed</p>
                <p className="font-semibold tabular-nums">{data.total_consumed}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

