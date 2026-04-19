"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { useCreateQueue, useDeleteQueue, useQueues } from "@/hooks/useQueues";

export function QueuesPanel() {
  const { data, isLoading } = useQueues();
  const create = useCreateQueue();
  const del = useDeleteQueue();
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("📺");

  async function onCreate() {
    if (!name.trim()) return;
    await create.mutateAsync({ name: name.trim(), icon });
    setName("");
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-2">Your queues</h2>
      <p className="text-xs text-white/60 mb-4">
        Named lists for different moods or occasions. Netflix won&apos;t let you do this — we will.
      </p>
      {isLoading ? (
        <div className="h-20 animate-pulse bg-surface-elevated rounded-md" />
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {data?.map((q) => (
            <li key={q.id} className="rounded-md bg-surface-elevated px-4 py-3 ring-1 ring-white/10 flex items-center gap-3">
              <span className="text-2xl">{q.icon ?? "📋"}</span>
              <div className="flex-1">
                <div className="text-sm font-semibold">{q.name}</div>
                <div className="text-xs text-white/50">{q.count} items</div>
              </div>
              <button
                onClick={() => { if (confirm(`Delete ${q.name}?`)) del.mutate(q.id); }}
                className="text-white/40 hover:text-white/70 text-sm"
                aria-label="delete"
              >×</button>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-6 flex gap-2 items-center">
        <input value={icon} onChange={(e) => setIcon(e.target.value)}
          className="w-12 text-center rounded bg-black/60 px-2 py-1 ring-1 ring-white/10" />
        <input value={name} onChange={(e) => setName(e.target.value)}
          placeholder="New queue name (e.g. Sunday Movies)"
          onKeyDown={(e) => { if (e.key === "Enter") onCreate(); }}
          className="flex-1 rounded bg-black/60 px-3 py-1.5 text-sm ring-1 ring-white/10" />
        <Button onClick={onCreate} disabled={create.isPending}>Add queue</Button>
      </div>
    </div>
  );
}
