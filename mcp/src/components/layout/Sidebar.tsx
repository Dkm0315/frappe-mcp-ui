/**
 * Sidebar Component
 * Dark, polished navigation sidebar with mode-specific navigation
 */
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/uiStore';
import { NavLink } from 'react-router-dom';
import type { UIMode } from '@/types';
import type { LucideIcon } from 'lucide-react';
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
  Shield,
  Code2,
  Workflow,
  Database,
  Terminal,
  Bug,
  MessageSquare,
  Zap,
  BookOpen,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
}

const adminNav: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Tools', href: '/tools', icon: Wrench },
  { name: 'Workflows', href: '/workflows', icon: GitBranch },
  { name: 'Feature Flags', href: '/feature-flags', icon: Shield },
  { name: 'History', href: '/history', icon: History },
  { name: 'Credits', href: '/credits', icon: CreditCard },
  { name: 'Discovery', href: '/discovery', icon: Compass },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const developerNav: NavItem[] = [
  { name: 'Script Studio', href: '/scripts', icon: Code2 },
  { name: 'Workflow Builder', href: '/workflow-builder', icon: Workflow },
  { name: 'Schema Manager', href: '/schema', icon: Database },
  { name: 'API Explorer', href: '/api-explorer', icon: Terminal },
  { name: 'Debug Console', href: '/debug', icon: Bug },
  { name: 'Tools', href: '/tools', icon: Wrench },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const assistantNav: NavItem[] = [
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Quick Actions', href: '/tools', icon: Zap },
  { name: 'My Activity', href: '/history', icon: History },
  { name: 'Discovery', href: '/discovery', icon: BookOpen },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const navigationByMode: Record<UIMode, NavItem[]> = {
  admin: adminNav,
  developer: developerNav,
  assistant: assistantNav,
};

const modeLabelMap: Record<UIMode, string> = {
  admin: 'Control Panel',
  developer: 'IDE',
  assistant: 'Assistant',
};

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, mode } = useUIStore();

  const navigation = navigationByMode[mode] || adminNav;
  const modeLabel = modeLabelMap[mode] || 'Control Panel';

  return (
    <div
      className={cn(
        'relative hidden md:flex flex-col transition-all duration-300',
        'bg-sidebar text-sidebar-foreground border-r border-sidebar-border',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Collapse Toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-6 z-10 size-6 rounded-full border border-sidebar-border bg-sidebar text-sidebar-foreground shadow-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
        onClick={toggleSidebar}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="size-3" />
        ) : (
          <ChevronLeft className="size-3" />
        )}
      </Button>

      {/* Mode Label */}
      <div
        className={cn(
          'flex items-center border-b border-sidebar-border px-4 py-3',
          sidebarCollapsed && 'justify-center px-2'
        )}
      >
        {!sidebarCollapsed ? (
          <span className="text-[11px] font-semibold uppercase tracking-widest text-sidebar-foreground/60">
            {modeLabel}
          </span>
        ) : (
          <span className="text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/60">
            {modeLabel.charAt(0)}
          </span>
        )}
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-3">
        <nav className="flex flex-col gap-0.5 px-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              end={item.href === '/'}
              className={({ isActive }) =>
                cn(
                  'relative flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
                  'text-sidebar-foreground/70 hover:text-sidebar-accent-foreground hover:bg-sidebar-accent',
                  isActive && 'text-sidebar-accent-foreground',
                  sidebarCollapsed && 'justify-center px-2'
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-lg bg-sidebar-accent"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <item.icon className="relative size-[18px] shrink-0" />
                  {!sidebarCollapsed && <span className="relative">{item.name}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bottom brand */}
      {!sidebarCollapsed && (
        <div className="border-t border-sidebar-border px-4 py-3">
          <p className="text-[10px] text-sidebar-foreground/30 uppercase tracking-wider">
            Frappe MCP
          </p>
        </div>
      )}
    </div>
  );
}
