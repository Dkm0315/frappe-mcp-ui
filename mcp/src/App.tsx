/**
 * Main App Component
 * Sets up React Query and routing
 */
import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Router } from './router';
import { Toaster } from 'sonner';
import { useUIStore } from '@/stores/uiStore';
import { api } from '@/lib/api';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useUIStore();

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);

  return <>{children}</>;
}

function SystemDetector({ children }: { children: React.ReactNode }) {
  const { setHasNextAI } = useUIStore();

  useEffect(() => {
    // Detect NextAI installation on app load
    async function detectSystem() {
      try {
        const health = await api.getSystemHealth();
        if (health?.nextai?.installed) {
          setHasNextAI(true);
        }
      } catch (error) {
        console.error('Failed to detect system health:', error);
      }
    }

    detectSystem();
  }, [setHasNextAI]);

  return <>{children}</>;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SystemDetector>
        <ThemeProvider>
          <Router />
          <Toaster position="top-right" richColors />
        </ThemeProvider>
      </SystemDetector>
    </QueryClientProvider>
  );
}
