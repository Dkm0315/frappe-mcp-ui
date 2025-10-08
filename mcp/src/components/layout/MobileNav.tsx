/**
 * MobileNav Component
 * Bottom navigation for mobile devices
 */
import { cn } from '@/lib/utils';
import { NavLink } from 'react-router-dom';
import { Home, Wrench, History, CreditCard } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Tools', href: '/tools', icon: Wrench },
  { name: 'History', href: '/history', icon: History },
  { name: 'Credits', href: '/credits', icon: CreditCard },
];

export function MobileNav() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background md:hidden">
      <nav className="flex items-center justify-around px-2 py-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center gap-1 rounded-md px-4 py-2 text-xs font-medium transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                isActive && 'text-primary'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn('size-5', isActive && 'text-primary')} />
                <span className={cn(isActive && 'text-primary')}>{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

