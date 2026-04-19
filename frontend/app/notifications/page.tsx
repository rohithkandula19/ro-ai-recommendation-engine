"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Notif { id: number; kind: string; title: string; body: string | null; link: string | null; read: boolean; created_at: string }

export default function NotificationsPage() {
  const qc = useQueryClient();
  const { data } = useQuery<{ items: Notif[] }>({
    queryKey: ["notifs"],
    queryFn: async () => (await api.get("/users/me/notifications")).data,
  });
  const readAll = useMutation({
    mutationFn: async () => { await api.post("/users/me/notifications/read-all"); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifs"] }),
  });

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-extrabold">Notifications</h1>
        <Button variant="ghost" onClick={() => readAll.mutate()}>Mark all read</Button>
      </div>
      {data?.items.length ? (
        <ul className="space-y-2">
          {data.items.map((n) => (
            <li key={n.id} className={`rounded-md p-4 ring-1 ring-white/10 ${n.read ? "bg-surface-elevated/50" : "bg-surface-elevated"}`}>
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm font-semibold">{n.title}</div>
                  {n.body && <div className="text-xs text-white/70 mt-1">{n.body}</div>}
                </div>
                <span className="text-[10px] text-white/40">{new Date(n.created_at).toLocaleString()}</span>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-white/60 text-sm">No notifications.</p>
      )}
    </div>
  );
}
