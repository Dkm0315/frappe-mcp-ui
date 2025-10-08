/**
 * Credit Store
 * Manages credit balance state
 */
import { create } from 'zustand';

interface CreditState {
  balance: number;
  totalPurchased: number;
  totalConsumed: number;
  isLoading: boolean;
  setCredits: (balance: number, totalPurchased: number, totalConsumed: number) => void;
  setLoading: (loading: boolean) => void;
  deductCredits: (amount: number) => void;
}

export const useCreditStore = create<CreditState>((set) => ({
  balance: 0,
  totalPurchased: 0,
  totalConsumed: 0,
  isLoading: false,
  
  setCredits: (balance, totalPurchased, totalConsumed) =>
    set({ balance, totalPurchased, totalConsumed }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  deductCredits: (amount) =>
    set((state) => ({
      balance: Math.max(0, state.balance - amount),
      totalConsumed: state.totalConsumed + amount,
    })),
}));

