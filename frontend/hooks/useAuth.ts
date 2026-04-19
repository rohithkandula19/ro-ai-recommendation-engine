"use client";

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, clearTokens, setTokens } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import type { User } from "@/types";

export function useAuth() {
  const router = useRouter();
  const { user, setUser, logout: clearStore, hydrated, setHydrated } = useAuthStore();

  useEffect(() => {
    if (!hydrated) setHydrated();
  }, [hydrated, setHydrated]);

  const fetchMe = useCallback(async () => {
    try {
      const r = await api.get<User>("/users/me");
      setUser(r.data);
    } catch {
      clearStore();
    }
  }, [setUser, clearStore]);

  const login = useCallback(async (email: string, password: string) => {
    const r = await api.post("/auth/login", { email, password });
    setTokens(r.data.access_token, r.data.refresh_token);
    await fetchMe();
    router.push("/browse");
  }, [fetchMe, router]);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const r = await api.post("/auth/register", {
      email, password, display_name: displayName,
    });
    setTokens(r.data.access_token, r.data.refresh_token);
    await fetchMe();
    router.push("/browse");
  }, [fetchMe, router]);

  const logout = useCallback(() => {
    clearTokens();
    clearStore();
    router.push("/login");
  }, [clearStore, router]);

  return { user, login, register, logout, fetchMe, hydrated };
}
