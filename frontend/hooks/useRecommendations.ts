"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { RecommendationSurface } from "@/types";

export function useRecommendations(surface: string, limit = 20) {
  return useQuery<RecommendationSurface>({
    queryKey: ["recommendations", surface, limit],
    queryFn: async () => {
      const r = await api.get(`/recommendations/${surface}`, { params: { limit } });
      return r.data;
    },
  });
}
