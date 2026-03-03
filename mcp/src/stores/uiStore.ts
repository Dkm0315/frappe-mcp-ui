/**
 * UI Store
 * Manages UI state, mode, and capability detection
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UIMode } from '@/types';

interface UIState {
  mode: UIMode;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  hasNextAI: boolean;
  serverScriptsEnabled: boolean;
  hasScriptManagerRole: boolean;
  setMode: (mode: UIMode) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setHasNextAI: (has: boolean) => void;
  setServerScriptsEnabled: (enabled: boolean) => void;
  setHasScriptManagerRole: (has: boolean) => void;
}

const VALID_MODES: UIMode[] = ['admin', 'developer', 'assistant'];

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      mode: 'admin',
      sidebarCollapsed: false,
      theme: 'system',
      hasNextAI: false,
      serverScriptsEnabled: false,
      hasScriptManagerRole: false,

      setMode: (mode) => set({ mode }),

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),

      setTheme: (theme) => set({ theme }),

      setHasNextAI: (has) => set({ hasNextAI: has }),

      setServerScriptsEnabled: (enabled) =>
        set({ serverScriptsEnabled: enabled }),

      setHasScriptManagerRole: (has) =>
        set({ hasScriptManagerRole: has }),
    }),
    {
      name: 'mcp-ui-preferences',
      // Migrate old mode values (simple/advanced/workflows) to new ones
      migrate: (persisted: any) => {
        if (persisted && !VALID_MODES.includes(persisted.mode)) {
          persisted.mode = 'admin';
        }
        return persisted;
      },
      version: 1,
    }
  )
);
