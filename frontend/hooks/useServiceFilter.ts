"use client";

import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

type MatchMap = Record<string, string[]>;

interface Ctx {
  onlyMine: boolean;
  setOnlyMine: (v: boolean) => void;
  subscriptions: string[];
  matches: MatchMap;
  registerIds: (ids: string[]) => void;
  isOnMyServices: (id: string) => boolean;
  topProviderFor: (id: string) => string | null;
}

const ServiceFilterContext = createContext<Ctx | null>(null);
const STORAGE_KEY = "ro:onlyMine";

export function ServiceFilterProvider({ children }: { children: ReactNode }) {
  const [onlyMine, setOnlyMineState] = useState(false);
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());
  const [matches, setMatches] = useState<MatchMap>({});

  useEffect(() => {
    try {
      const v = window.localStorage.getItem(STORAGE_KEY);
      if (v === "1") setOnlyMineState(true);
    } catch {}
  }, []);

  const setOnlyMine = useCallback((v: boolean) => {
    setOnlyMineState(v);
    try { window.localStorage.setItem(STORAGE_KEY, v ? "1" : "0"); } catch {}
  }, []);

  const { data: mine } = useQuery<{ providers: string[] }>({
    queryKey: ["providers:mine"],
    queryFn: async () => (await api.get("/availability/me/subscriptions")).data,
    staleTime: 60_000,
  });
  const subscriptions = mine?.providers ?? [];

  const matchMut = useMutation({
    mutationFn: async (ids: string[]) =>
      (await api.post("/availability/match", { content_ids: ids, region: "US" })).data as { matches: MatchMap },
    onSuccess: (data) => {
      if (data?.matches) setMatches((prev) => ({ ...prev, ...data.matches }));
    },
  });

  const registerIds = useCallback((ids: string[]) => {
    setPendingIds((prev) => {
      const next = new Set(prev);
      let added = false;
      for (const id of ids) if (!next.has(id) && !matches[id]) { next.add(id); added = true; }
      return added ? next : prev;
    });
  }, [matches]);

  useEffect(() => {
    if (!subscriptions.length || pendingIds.size === 0) return;
    const ids = Array.from(pendingIds);
    setPendingIds(new Set());
    matchMut.mutate(ids);
  }, [pendingIds, subscriptions.length]);

  const value = useMemo<Ctx>(() => ({
    onlyMine,
    setOnlyMine,
    subscriptions,
    matches,
    registerIds,
    isOnMyServices: (id) => (matches[id]?.length ?? 0) > 0,
    topProviderFor: (id) => matches[id]?.[0] ?? null,
  }), [onlyMine, setOnlyMine, subscriptions, matches, registerIds]);

  return createElement(ServiceFilterContext.Provider, { value }, children);
}

export function useServiceFilter() {
  const ctx = useContext(ServiceFilterContext);
  if (!ctx) {
    return {
      onlyMine: false,
      setOnlyMine: () => {},
      subscriptions: [] as string[],
      matches: {} as MatchMap,
      registerIds: () => {},
      isOnMyServices: () => false,
      topProviderFor: () => null,
    };
  }
  return ctx;
}
