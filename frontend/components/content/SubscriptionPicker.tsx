"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

const DEFAULT_PROVIDERS = [
  "Netflix", "Amazon Prime Video", "Max", "Disney Plus", "Hulu",
  "Apple TV Plus", "Peacock", "Paramount Plus", "Starz", "Showtime",
  "AMC Plus", "Crunchyroll", "Tubi TV", "Pluto TV", "Freevee",
];

export function SubscriptionPicker({ onSaved }: { onSaved?: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const { data: known } = useQuery<{ providers: string[] }>({
    queryKey: ["providers:known"],
    queryFn: async () => (await api.get("/availability/providers")).data,
  });
  const { data: mine } = useQuery<{ providers: string[] }>({
    queryKey: ["providers:mine"],
    queryFn: async () => (await api.get("/availability/me/subscriptions")).data,
  });

  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (mine?.providers) setSelected(new Set(mine.providers));
  }, [mine?.providers]);

  const providers = known?.providers?.length ? known.providers : DEFAULT_PROVIDERS;

  const save = useMutation({
    mutationFn: async () => (await api.put("/availability/me/subscriptions", { providers: Array.from(selected) })).data,
    onSuccess: () => {
      toast.show("Services saved", "success");
      qc.invalidateQueries({ queryKey: ["providers:mine"] });
      qc.invalidateQueries({ queryKey: ["browse"] });
      onSaved?.();
    },
    onError: () => toast.show("Could not save — try again"),
  });

  function toggle(p: string) {
    const next = new Set(selected);
    if (next.has(p)) next.delete(p);
    else next.add(p);
    setSelected(next);
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {providers.map((p) => {
          const on = selected.has(p);
          return (
            <button
              key={p}
              type="button"
              onClick={() => toggle(p)}
              aria-pressed={on}
              className={`rounded-lg px-3 py-2.5 text-sm text-left ring-1 transition ${
                on
                  ? "bg-brand/20 ring-brand text-white"
                  : "bg-white/[0.04] ring-white/10 text-white/75 hover:bg-white/[0.08]"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate">{p}</span>
                <span className={`text-[10px] ${on ? "text-brand" : "text-white/30"}`}>
                  {on ? "●" : "○"}
                </span>
              </div>
            </button>
          );
        })}
      </div>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs text-white/50">{selected.size} selected</span>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>Clear</Button>
          <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}
