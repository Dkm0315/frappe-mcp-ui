/**
 * Keyboard Shortcuts Hook
 * Provides keyboard shortcuts for common actions
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface ShortcutHandlers {
  onSearch?: () => void;
  onCreateNew?: () => void;
  onSettings?: () => void;
  onHelp?: () => void;
  onToggleSidebar?: () => void;
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers = {}) {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if typing in input/textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Cmd/Ctrl + K - Search
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        handlers.onSearch?.();
      }

      // Cmd/Ctrl + N - Create New
      if ((event.metaKey || event.ctrlKey) && event.key === 'n') {
        event.preventDefault();
        handlers.onCreateNew?.();
      }

      // Cmd/Ctrl + , - Settings
      if ((event.metaKey || event.ctrlKey) && event.key === ',') {
        event.preventDefault();
        navigate('/settings');
      }

      // Cmd/Ctrl + / - Help/Shortcuts
      if ((event.metaKey || event.ctrlKey) && event.key === '/') {
        event.preventDefault();
        handlers.onHelp?.();
      }

      // Cmd/Ctrl + B - Toggle Sidebar
      if ((event.metaKey || event.ctrlKey) && event.key === 'b') {
        event.preventDefault();
        handlers.onToggleSidebar?.();
      }

      // Cmd/Ctrl + 1-6 - Navigation
      if ((event.metaKey || event.ctrlKey) && event.key >= '1' && event.key <= '6') {
        event.preventDefault();
        const routes = ['/', '/tools', '/history', '/credits', '/discovery', '/settings'];
        const index = parseInt(event.key) - 1;
        if (routes[index]) {
          navigate(routes[index]);
        }
      }

      // ESC - Close modals (handled by components)
      // ? - Show shortcuts
      if (event.key === '?' && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        handlers.onHelp?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handlers, navigate]);
}

// Export shortcut info for help modal
export const KEYBOARD_SHORTCUTS = [
  {
    category: 'Navigation',
    shortcuts: [
      { keys: ['Cmd', '1'], description: 'Go to Dashboard' },
      { keys: ['Cmd', '2'], description: 'Go to Tools' },
      { keys: ['Cmd', '3'], description: 'Go to History' },
      { keys: ['Cmd', '4'], description: 'Go to Credits' },
      { keys: ['Cmd', '5'], description: 'Go to Discovery' },
      { keys: ['Cmd', '6'], description: 'Go to Settings' },
    ],
  },
  {
    category: 'Actions',
    shortcuts: [
      { keys: ['Cmd', 'K'], description: 'Quick Search' },
      { keys: ['Cmd', 'N'], description: 'Create New' },
      { keys: ['Cmd', ','], description: 'Settings' },
      { keys: ['Cmd', 'B'], description: 'Toggle Sidebar' },
      { keys: ['ESC'], description: 'Close Modal/Dialog' },
    ],
  },
  {
    category: 'Help',
    shortcuts: [
      { keys: ['?'], description: 'Show Keyboard Shortcuts' },
      { keys: ['Cmd', '/'], description: 'Help' },
    ],
  },
];

