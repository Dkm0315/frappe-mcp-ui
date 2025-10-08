/**
 * Authentication Store
 * Manages user authentication state
 */
import { create } from 'zustand';

interface AuthState {
  user: string | null;
  fullName: string | null;
  userImage: string | null;
  siteName: string | null;
  isAuthenticated: boolean;
  setUser: (user: string, fullName?: string, userImage?: string, siteName?: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: window.boot_data?.user || null,
  fullName: window.boot_data?.full_name || null,
  userImage: window.boot_data?.user_image || null,
  siteName: window.boot_data?.site_name || null,
  isAuthenticated: !!window.boot_data?.user && window.boot_data.user !== 'Guest',
  
  setUser: (user, fullName, userImage, siteName) =>
    set({
      user,
      fullName: fullName || null,
      userImage: userImage || null,
      siteName: siteName || null,
      isAuthenticated: !!user && user !== 'Guest',
    }),
  
  logout: () =>
    set({
      user: null,
      fullName: null,
      userImage: null,
      siteName: null,
      isAuthenticated: false,
    }),
}));

