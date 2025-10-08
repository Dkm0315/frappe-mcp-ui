/**
 * AppShell Component
 * Main layout wrapper with sidebar, topbar, and content area
 */
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { MobileNav } from './MobileNav';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import { useUIStore } from '@/stores/uiStore';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

export function AppShell() {
  const { mode, toggleSidebar } = useUIStore();
  const [showShortcuts, setShowShortcuts] = useState(false);

  useKeyboardShortcuts({
    onHelp: () => setShowShortcuts(true),
    onToggleSidebar: () => toggleSidebar(),
  });

  return (
    <>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar - only in advanced mode */}
        {mode === 'advanced' && <Sidebar />}

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />
          
          <main className="flex-1 overflow-y-auto bg-muted/30 pb-20 md:pb-4">
            <div className="container mx-auto p-4 md:p-6">
              <Outlet />
            </div>
          </main>
        </div>

        {/* Mobile Navigation */}
        <MobileNav />
      </div>

      {/* Keyboard Shortcuts Modal */}
      <KeyboardShortcutsModal 
        open={showShortcuts} 
        onClose={() => setShowShortcuts(false)} 
      />
    </>
  );
}

