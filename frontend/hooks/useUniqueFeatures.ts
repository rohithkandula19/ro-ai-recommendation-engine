"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface VibeVector {
  pace: number;
  emotion: number;
  darkness: number;
  humor: number;
  complexity: number;
  spectacle: number;
}

export interface TasteDNA {
  user_id: string;
  dna: VibeVector;
  samples: number;
}

export interface RankerSignal {
  name: string;
  value: number;
  description: string;
}

export interface Explain {
  content_id: string;
  signals: RankerSignal[];
  dominant_reason: string;
  ai_summary: string | null;
}

export function useTasteDNA() {
  return useQuery<TasteDNA>({
    queryKey: ["taste-dna"],
    queryFn: async () => (await api.get("/users/me/taste-dna")).data,
  });
}

export function useMoodRecs(chill_tense: number, light_thoughtful: number, limit = 12) {
  return useQuery({
    queryKey: ["mood", chill_tense, light_thoughtful, limit],
    queryFn: async () =>
      (await api.post("/recommendations/mood", { chill_tense, light_thoughtful, limit })).data,
  });
}

export function useTimeBudget(minutes: number, limit = 12) {
  return useQuery({
    queryKey: ["time-budget", minutes, limit],
    queryFn: async () =>
      (await api.post("/recommendations/time-budget", { minutes, limit, tolerance_pct: 25 })).data,
    enabled: minutes > 0,
  });
}

export function useExplain(contentId: string | null) {
  return useQuery<Explain>({
    queryKey: ["explain", contentId],
    queryFn: async () => (await api.get(`/recommendations/explain/${contentId}`)).data,
    enabled: !!contentId,
  });
}

export function useCoViewer(userIds: string[], limit = 12) {
  return useQuery({
    queryKey: ["co-viewer", userIds, limit],
    queryFn: async () =>
      (await api.post("/recommendations/co-viewer", { user_ids: userIds, limit })).data,
    enabled: userIds.length >= 1,
  });
}

export function useFeedback() {
  return useMutation({
    mutationFn: async (payload: { content_id: string; surface: string; feedback: number; reason?: string }) => {
      await api.post("/recommendations/feedback", payload);
    },
  });
}

export function useNLSearch() {
  return useMutation({
    mutationFn: async (q: string) => (await api.post("/search/nl", { query: q, limit: 20 })).data,
  });
}
