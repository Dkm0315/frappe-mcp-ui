/**
 * PurchaseModal Component
 * Credit package purchase flow
 */
import { useState } from 'react';
import { useCreditPackages, usePurchaseCredits } from '@/hooks/useCredits';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Check, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import type { CreditPackage } from '@/types';

interface PurchaseModalProps {
  trigger?: React.ReactNode;
}

export function PurchaseModal({ trigger }: PurchaseModalProps) {
  const [open, setOpen] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState<CreditPackage | null>(null);
  const { data: packages, isLoading } = useCreditPackages();
  const purchaseMutation = usePurchaseCredits();

  const handlePurchase = () => {
    if (!selectedPackage) return;

    purchaseMutation.mutate(selectedPackage.name, {
      onSuccess: () => {
        setOpen(false);
        setSelectedPackage(null);
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Sparkles className="mr-2 size-4" />
            Purchase Credits
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Purchase Credits</DialogTitle>
          <DialogDescription>
            Choose a credit package to continue using MCP tools
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-48" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {packages?.map((pkg) => (
              <motion.div
                key={pkg.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Card
                  className={`cursor-pointer transition-all ${
                    selectedPackage?.name === pkg.name
                      ? 'border-primary ring-2 ring-primary/20'
                      : 'hover:border-primary/50'
                  }`}
                  onClick={() => setSelectedPackage(pkg)}
                >
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{pkg.package_name}</span>
                      {selectedPackage?.name === pkg.name && (
                        <Check className="size-5 text-primary" />
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-3xl font-bold">{pkg.credits}</p>
                        <p className="text-sm text-muted-foreground">credits</p>
                      </div>
                      <Badge variant="secondary" className="w-full justify-center">
                        ${pkg.price}
                      </Badge>
                      {pkg.description && (
                        <p className="text-xs text-muted-foreground">{pkg.description}</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handlePurchase}
            disabled={!selectedPackage || purchaseMutation.isPending}
          >
            {purchaseMutation.isPending ? 'Processing...' : 'Purchase'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

