"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Flag { key: string; enabled: boolean; rollout_pct: number; updated_at: string }

export default function FeatureFlagsAdmin() {
  const qc = useQueryClient();
  const [newKey, setNewKey] = useState("");
  const { data } = useQuery<{ items: Flag[] }>({
    queryKey: ["flags-admin"],
    queryFn: async () => (await api.get("/admin/feature-flags")).data,
  });
  const upsert = useMutation({
    mutationFn: async ({ key, enabled, rollout_pct }: Flag) =>
      (await api.put(`/admin/feature-flags/${key}?enabled=${enabled}&rollout_pct=${rollout_pct}`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["flags-admin"] }),
  });

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Feature flags</h1>
      <p className="text-sm text-white/60 mt-1">Bucket-based rollout by user hash. 100% = all users.</p>
      <div className="mt-6 space-y-2">
        {data?.items.map((f) => (
          <div key={f.key} className="flex items-center gap-3 rounded-md bg-surface-elevated ring-1 ring-white/10 px-4 py-3">
            <code className="flex-1 text-sm">{f.key}</code>
            <input type="checkbox" checked={f.enabled}
              onChange={(e) => upsert.mutate({ ...f, enabled: e.target.checked })} />
            <input type="number" min={0} max={100} value={f.rollout_pct}
              onChange={(e) => upsert.mutate({ ...f, rollout_pct: Number(e.target.value) })}
              className="w-16 rounded bg-black/60 px-2 py-1 text-sm ring-1 ring-white/10 text-right" />
            <span className="text-xs text-white/40 w-8">%</span>
          </div>
        ))}
      </div>
      <div className="mt-8 flex gap-2">
        <input value={newKey} onChange={(e) => setNewKey(e.target.value)}
          placeholder="new flag key (e.g. chat_v2)"
          className="flex-1 rounded bg-black/60 px-3 py-2 text-sm ring-1 ring-white/10" />
        <Button onClick={() => { if (newKey.trim()) upsert.mutate({ key: newKey.trim(), enabled: false, rollout_pct: 0, updated_at: "" }); setNewKey(""); }}>
          Add flag
        </Button>
      </div>
    </div>
  );
}
