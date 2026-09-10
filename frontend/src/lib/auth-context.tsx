import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";

export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role?: string;
  created_at?: string;
}

export interface UserSettings {
  id?: string;
  user_id?: string;
  theme: string;
  default_min_similarity: number;
  default_top_k: number;
  preferred_model: string;
  auto_save_history: boolean;
  email_notifications?: boolean;
  updated_at?: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface ProfileUpdatePayload {
  full_name?: string;
  bio?: string;
  avatar_url?: string;
}

export interface AuthContextType {
  user: User | null;
  settings: UserSettings | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  authModalTab: "login" | "register";
  openAuthModal: (tab?: "login" | "register") => void;
  closeAuthModal: () => void;
  login: (identifier: string, password: string) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: ProfileUpdatePayload) => Promise<void>;
  updateSettings: (data: Partial<UserSettings>) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const TOKEN_KEY = "auth_token";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("login");

  const openAuthModal = useCallback((tab: "login" | "register" = "login") => {
    setAuthModalTab(tab);
    setIsAuthModalOpen(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setIsAuthModalOpen(false);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setUser(null);
      setSettings(null);
      setIsLoading(false);
      return;
    }

    try {
      const res = await api.auth.me();
      if (res && res.user) {
        setUser(res.user);
        if (res.settings) {
          setSettings(res.settings as UserSettings);
        }
      } else {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
        setSettings(null);
      }
    } catch {
      // Token invalid or expired
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
      setSettings(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshProfile();
  }, [refreshProfile]);

  const login = useCallback(
    async (identifier: string, password: string) => {
      const res = await api.auth.login(identifier, password);
      if (res && res.access_token) {
        if (typeof window !== "undefined") {
          localStorage.setItem(TOKEN_KEY, res.access_token);
        }
        setUser(res.user);
        setIsAuthModalOpen(false);

        // Fetch complete profile & settings
        try {
          const profile = await api.auth.me();
          if (profile?.settings) {
            setSettings(profile.settings as UserSettings);
          }
        } catch {
          // Ignore settings fetch failure
        }

        toast.success(`Welcome back, ${res.user.full_name || res.user.username}!`);
      } else {
        throw new Error("Invalid response from server.");
      }
    },
    []
  );

  const register = useCallback(
    async (data: RegisterPayload) => {
      const res = await api.auth.register(data);
      if (res && res.access_token) {
        if (typeof window !== "undefined") {
          localStorage.setItem(TOKEN_KEY, res.access_token);
        }
        setUser(res.user);
        setIsAuthModalOpen(false);

        try {
          const profile = await api.auth.me();
          if (profile?.settings) {
            setSettings(profile.settings as UserSettings);
          }
        } catch {
          // Ignore settings fetch failure
        }

        toast.success(`Account created successfully. Welcome, ${res.user.full_name || res.user.username}!`);
      } else {
        throw new Error("Failed to create account.");
      }
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem(TOKEN_KEY);
      }
      setUser(null);
      setSettings(null);
      toast.info("You have been signed out.");
    }
  }, []);

  const updateProfile = useCallback(
    async (data: ProfileUpdatePayload) => {
      const res = await api.user.updateProfile(data);
      if (res?.user) {
        setUser(res.user);
        if (res.settings) {
          setSettings(res.settings as UserSettings);
        }
        toast.success("Profile updated successfully.");
      }
    },
    []
  );

  const updateSettings = useCallback(
    async (data: Partial<UserSettings>) => {
      const res = await api.user.updateSettings(data);
      if (res) {
        setSettings(res as UserSettings);
        toast.success("Preferences updated successfully.");
      }
    },
    []
  );

  const value: AuthContextType = {
    user,
    settings,
    isAuthenticated: !!user,
    isLoading,
    isAuthModalOpen,
    authModalTab,
    openAuthModal,
    closeAuthModal,
    login,
    register,
    logout,
    updateProfile,
    updateSettings,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
