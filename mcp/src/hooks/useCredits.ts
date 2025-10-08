/**
 * Hook to manage credit balance and usage
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useCreditStore } from '@/stores/creditStore';
import { toast } from 'sonner';
import type { CreditBalance, UsageLog, CreditPackage } from '@/types';

export function useCredits() {
  const { setCredits, setLoading } = useCreditStore();

  return useQuery({
    queryKey: ['credits'],
    queryFn: async () => {
      setLoading(true);
      const response = await api.getCreditBalance();
      const balance = response as CreditBalance;
      setCredits(balance.balance, balance.total_purchased, balance.total_consumed);
      setLoading(false);
      return balance;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

export function useUsageHistory(limit = 50) {
  return useQuery({
    queryKey: ['usage-history', limit],
    queryFn: async () => {
      const response = await api.getUsageHistory(limit);
      return response as UsageLog[];
    },
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useCreditPackages() {
  return useQuery({
    queryKey: ['credit-packages'],
    queryFn: async () => {
      const response = await api.getAvailablePackages();
      return response as CreditPackage[];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function usePurchaseCredits() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (packageName: string) => {
      return await api.purchaseCredits(packageName);
    },
    
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['credits'] });
      toast.success('Credits purchased successfully!', {
        description: `Added ${data.package} credits. New balance: ${data.new_balance}`,
      });
    },
    
    onError: (error: Error) => {
      toast.error('Purchase failed', {
        description: error.message,
      });
    },
  });
}

