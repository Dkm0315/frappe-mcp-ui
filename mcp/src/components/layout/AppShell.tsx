/**
 * AppShell Component
 * Main layout wrapper with sidebar, topbar, and content area
 */
import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { MobileNav } from './MobileNav';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import { useUIStore } from '@/stores/uiStore';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

export function AppShell() {
  const { toggleSidebar } = useUIStore();
  const [showShortcuts, setShowShortcuts] = useState(false);
  const location = useLocation();

  useKeyboardShortcuts({
    onHelp: () => setShowShortcuts(true),
    onToggleSidebar: () => toggleSidebar(),
  });

  return (
    <>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar - always visible, navigation adapts per mode */}
        <Sidebar />

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopBar />

          <main className="flex-1 overflow-y-auto bg-muted/30 pb-20 md:pb-4">
            <div className="container mx-auto p-4 md:p-6">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >
                <Outlet />
              </motion.div>
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

