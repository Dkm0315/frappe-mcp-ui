/**
 * Credits Page
 * Manage credit balance and purchase packages
 */
import { CreditBalance } from '@/components/credits/CreditBalance';
import { CreditHistory } from '@/components/credits/CreditHistory';
import { PurchaseModal } from '@/components/credits/PurchaseModal';

export function Credits() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Credit Management</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your credit balance and view usage history
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-1">
          <CreditBalance />
          <PurchaseModal trigger={
            <button className="mt-4 inline-flex h-9 w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90">
              Purchase Credits
            </button>
          } />
        </div>

        <div className="md:col-span-2">
          <CreditHistory />
        </div>
      </div>
    </div>
  );
}

