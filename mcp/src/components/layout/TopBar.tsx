/**
 * TopBar Component
 * Header with credit balance, user menu, and mode switcher
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
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { Menu, Settings, LogOut, Sparkles, LayoutGrid } from 'lucide-react';

export function TopBar() {
  const { user, fullName, userImage } = useAuthStore();
  const { mode, setMode, toggleSidebar, sidebarCollapsed } = useUIStore();

  const handleLogout = () => {
    window.location.href = '/api/method/logout';
  };

  const initials = fullName
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase() || user?.charAt(0).toUpperCase();

  return (
    <div className="sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background px-4 md:px-6">
      {/* Left: Mobile menu + Logo */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={toggleSidebar}
        >
          <Menu className="size-5" />
        </Button>
        
        <div className="flex items-center gap-2">
          <Sparkles className="size-6 text-primary" />
          <h1 className="text-xl font-bold">MCP Tools</h1>
        </div>
      </div>

      {/* Right: Credit Balance + Mode Switcher + User Menu */}
      <div className="flex items-center gap-3">
        {/* Credit Balance */}
        <CreditBalance variant="compact" />

        {/* Mode Switcher */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMode(mode === 'simple' ? 'advanced' : 'simple')}
          className="hidden md:flex items-center gap-2"
        >
          <LayoutGrid className="size-4" />
          <span className="text-xs">
            {mode === 'simple' ? 'Simple' : 'Advanced'}
          </span>
          <Badge variant="secondary" className="ml-1">
            {mode === 'simple' ? 'Easy' : 'Pro'}
          </Badge>
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="size-9">
                <AvatarImage src={userImage || undefined} alt={fullName || user || ''} />
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{fullName || user}</p>
                <p className="text-xs text-muted-foreground">{user}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="md:hidden" onClick={() => setMode(mode === 'simple' ? 'advanced' : 'simple')}>
              <LayoutGrid className="mr-2 size-4" />
              Switch to {mode === 'simple' ? 'Advanced' : 'Simple'} Mode
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => window.location.href = '/app'}>
              <Settings className="mr-2 size-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 size-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

