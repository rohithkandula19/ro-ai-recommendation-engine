"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SearchResult } from "@/types";

export function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export function useSearch(query: string) {
  const debounced = useDebounced(query, 300);
  return useQuery<{ query: string; results: SearchResult[] }>({
    queryKey: ["search", debounced],
    queryFn: async () => {
      if (!debounced.trim()) return { query: debounced, results: [] };
      const r = await api.get("/search", { params: { q: debounced, limit: 20 } });
      return r.data;
    },
    enabled: debounced.length >= 0,
  });
}
