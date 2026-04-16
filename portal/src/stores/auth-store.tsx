"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { authService } from "@/services/auth";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id?: string;
  avatar_url?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  login: async () => ({}) as unknown as User,
  logout: () => {},
  updateUser: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    authService
      .me()
      .then((u) => setUser(u as User))
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authService.login(email, password);
    localStorage.setItem("access_token", res.access_token);
    localStorage.setItem("refresh_token", res.refresh_token);
    const u = res.user as User;
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(() => {
    authService.logout().catch(() => {});
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  }, []);

  const updateUser = useCallback((updates: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...updates } : prev));
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
