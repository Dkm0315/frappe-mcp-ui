/**
 * TopBar Component
 * Polished header with credit balance, mode switcher, and user menu
 */
import { CreditBalance } from '@/components/credits/CreditBalance';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import {
  Menu,
  Settings,
  LogOut,
  Shield,
  Code2,
  MessageSquare,
  Check,
  Hexagon,
} from 'lucide-react';
import type { UIMode } from '@/types';

const modes: { value: UIMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: 'admin', label: 'Admin', icon: Shield },
  { value: 'developer', label: 'IDE', icon: Code2 },
  { value: 'assistant', label: 'Chat', icon: MessageSquare },
];

export function TopBar() {
  const { user, fullName, userImage } = useAuthStore();
  const { mode, setMode, toggleSidebar } = useUIStore();

  const handleLogout = () => {
    window.location.href = '/api/method/logout';
  };

  const initials = fullName
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase() || user?.charAt(0).toUpperCase();

  return (
    <div className="sticky top-0 z-40 flex h-14 items-center justify-between border-b bg-background/80 backdrop-blur-md px-4 md:px-6">
      {/* Left: Mobile menu + Logo */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden size-8"
          onClick={toggleSidebar}
        >
          <Menu className="size-4" />
        </Button>

        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-lg bg-primary">
            <Hexagon className="size-4 text-primary-foreground" />
          </div>
          <h1 className="text-sm font-semibold tracking-tight">Frappe MCP</h1>
        </div>
      </div>

      {/* Right: Credit Balance + Mode Switcher + User Menu */}
      <div className="flex items-center gap-2">
        {/* Credit Balance */}
        <CreditBalance variant="compact" />

        {/* Segmented Mode Switcher with animated pill */}
        <div className="hidden md:flex items-center rounded-lg bg-muted p-0.5 relative">
          {modes.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              type="button"
              onClick={() => setMode(value)}
              className={cn(
                'relative inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors z-10',
                mode === value
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {mode === value && (
                <motion.div
                  layoutId="mode-pill"
                  className="absolute inset-0 rounded-md bg-background shadow-sm ring-1 ring-border/50"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative flex items-center gap-1.5">
                <Icon className="size-3.5" />
                <span>{label}</span>
              </span>
            </button>
          ))}
        </div>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="size-8">
                <AvatarImage src={userImage || undefined} alt={fullName || user || ''} />
                <AvatarFallback className="text-xs bg-primary/10 text-primary">{initials}</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-0.5">
                <p className="text-sm font-medium">{fullName || user}</p>
                <p className="text-[11px] text-muted-foreground">{user}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {modes.map(({ value, label, icon: Icon }) => (
              <DropdownMenuItem
                key={value}
                className="md:hidden"
                onClick={() => setMode(value)}
              >
                <Icon className="mr-2 size-4" />
                {label}
                {mode === value && <Check className="ml-auto size-4" />}
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator className="md:hidden" />
            <DropdownMenuItem onClick={() => (window.location.href = '/app')}>
              <Settings className="mr-2 size-4" />
              Frappe Desk
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
              <LogOut className="mr-2 size-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
