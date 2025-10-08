/**
 * UI Store
 * Manages UI state and preferences
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UIMode } from '@/types';

interface UIState {
  mode: UIMode;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  hasNextAI: boolean;
  setMode: (mode: UIMode) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setHasNextAI: (has: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      mode: 'simple',
      sidebarCollapsed: false,
      theme: 'system',
      hasNextAI: false,
      
      setMode: (mode) => set({ mode }),
      
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),
      
      setTheme: (theme) => set({ theme }),
      
      setHasNextAI: (has) => set({ hasNextAI: has }),
    }),
    {
      name: 'mcp-ui-preferences',
    }
  )
);

