/**
 * Sidebar Component
 * Navigation sidebar for advanced mode
 */
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useUIStore } from '@/stores/uiStore';
import { NavLink } from 'react-router-dom';
import {
  Home,
  Wrench,
  History,
  CreditCard,
  Settings,
  ChevronLeft,
  ChevronRight,
  Compass,
  GitBranch,
} from 'lucide-react';

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, hasNextAI } = useUIStore();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Tools', href: '/tools', icon: Wrench },
    ...(hasNextAI ? [{ name: 'Workflows', href: '/workflows', icon: GitBranch }] : []),
    { name: 'History', href: '/history', icon: History },
    { name: 'Credits', href: '/credits', icon: CreditCard },
    { name: 'Discovery', href: '/discovery', icon: Compass },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div
      className={cn(
        'relative hidden md:flex flex-col border-r bg-background transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Collapse Toggle */}
      <Button
        variant="ghost"
        size="icon-sm"
        className="absolute -right-3 top-6 z-10 size-6 rounded-full border bg-background shadow-sm"
        onClick={toggleSidebar}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="size-3" />
        ) : (
          <ChevronLeft className="size-3" />
        )}
      </Button>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-4">
        <nav className="flex flex-col gap-1 px-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  'hover:bg-accent hover:text-accent-foreground',
                  isActive && 'bg-accent text-accent-foreground',
                  sidebarCollapsed && 'justify-center px-2'
                )
              }
            >
              <item.icon className="size-5 shrink-0" />
              {!sidebarCollapsed && <span>{item.name}</span>}
            </NavLink>
          ))}
        </nav>
      </ScrollArea>
    </div>
  );
}

