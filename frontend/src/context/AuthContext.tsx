import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import {
  getCurrentUser,
  loginUser,
  registerUser,
  logoutUser,
  getAuthToken,
  syncWatchlist,
} from '../utils/api';

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  authModalMode: 'login' | 'register';
  openAuthModal: (mode?: 'login' | 'register') => void;
  closeAuthModal: () => void;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  const syncLocalWishlistToBackend = useCallback(async () => {
    try {
      const stored = localStorage.getItem('pricewise_beauty_wishlist');
      if (stored) {
        const itemIds: string[] = JSON.parse(stored);
        if (Array.isArray(itemIds) && itemIds.length > 0) {
          const syncItems = itemIds.map((id) => {
            const numericId = parseInt(id.replace('prod-', ''), 10);
            return {
              product_id: isNaN(numericId) ? 1 : numericId,
            };
          });
          await syncWatchlist(syncItems);
        }
      }
    } catch {
      // Non-blocking sync failure
    }
  }, []);

  const refreshUser = useCallback(async () => {
    if (!getAuthToken()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const openAuthModal = (mode: 'login' | 'register' = 'login') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const handleLogin = async (email: string, password: string) => {
    setIsLoading(true);
    const result = await loginUser(email, password);
    if (result.success && result.user) {
      setUser(result.user);
      setIsAuthModalOpen(false);
      // Auto-sync anonymous wishlist upon successful login
      await syncLocalWishlistToBackend();
      setIsLoading(false);
      return { success: true };
    }
    setIsLoading(false);
    return { success: false, error: result.error || 'Login failed' };
  };

  const handleRegister = async (name: string, email: string, password: string) => {
    setIsLoading(true);
    const result = await registerUser(name, email, password);
    if (result.success && result.user) {
      setUser(result.user);
      setIsAuthModalOpen(false);
      // Auto-sync anonymous wishlist upon successful registration
      await syncLocalWishlistToBackend();
      setIsLoading(false);
      return { success: true };
    }
    setIsLoading(false);
    return { success: false, error: result.error || 'Registration failed' };
  };

  const handleLogout = async () => {
    setIsLoading(true);
    await logoutUser();
    setUser(null);
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthModalOpen,
        authModalMode,
        openAuthModal,
        closeAuthModal,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
