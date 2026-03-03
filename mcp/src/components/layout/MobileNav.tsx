/**
 * MobileNav Component
 * Bottom navigation for mobile devices - adapts per mode
 */
import { cn } from '@/lib/utils';
import { NavLink } from 'react-router-dom';
import { useUIStore } from '@/stores/uiStore';
import type { UIMode } from '@/types';
import {
  Home, Wrench, History, CreditCard,
  Code2, Workflow, Database, Terminal,
  MessageSquare, Zap, BookOpen,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
}

const mobileNavByMode: Record<UIMode, NavItem[]> = {
  admin: [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Tools', href: '/tools', icon: Wrench },
    { name: 'History', href: '/history', icon: History },
    { name: 'Credits', href: '/credits', icon: CreditCard },
  ],
  developer: [
    { name: 'Scripts', href: '/scripts', icon: Code2 },
    { name: 'Workflows', href: '/workflow-builder', icon: Workflow },
    { name: 'Schema', href: '/schema', icon: Database },
    { name: 'API', href: '/api-explorer', icon: Terminal },
  ],
  assistant: [
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Actions', href: '/tools', icon: Zap },
    { name: 'Activity', href: '/history', icon: History },
    { name: 'Explore', href: '/discovery', icon: BookOpen },
  ],
};

export function MobileNav() {
  const { mode } = useUIStore();
  const navigation = mobileNavByMode[mode] || mobileNavByMode.admin;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/80 backdrop-blur-md md:hidden">
      <nav className="flex items-center justify-around px-2 py-1.5">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            end={item.href === '/'}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 text-[10px] font-medium transition-colors',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn('size-4.5', isActive && 'text-primary')} />
                <span>{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
