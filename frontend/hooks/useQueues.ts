"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Queue { id: string; name: string; icon: string | null; count: number }

export function useQueues() {
  return useQuery<Queue[]>({
    queryKey: ["queues"],
    queryFn: async () => (await api.get("/users/me/queues")).data,
  });
}

export function useCreateQueue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; icon?: string }) =>
      (await api.post("/users/me/queues", body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["queues"] }),
  });
}

export function useDeleteQueue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (queueId: string) => { await api.delete(`/users/me/queues/${queueId}`); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["queues"] }),
  });
}

export function useQueueItems(queueId: string | null) {
  return useQuery({
    queryKey: ["queue-items", queueId],
    queryFn: async () => (await api.get(`/users/me/queues/${queueId}/items`)).data,
    enabled: !!queueId,
  });
}

export function useAddToQueue() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ queueId, contentId }: { queueId: string; contentId: string }) => {
      await api.post(`/users/me/queues/${queueId}/items/${contentId}`);
    },
    onSuccess: (_, v) => {
      qc.invalidateQueries({ queryKey: ["queues"] });
      qc.invalidateQueries({ queryKey: ["queue-items", v.queueId] });
    },
  });
}

export function useDNATimeline(days = 90) {
  return useQuery({
    queryKey: ["dna-timeline", days],
    queryFn: async () => (await api.get(`/users/me/dna-timeline?days=${days}`)).data,
  });
}
