"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export default function StreakPage() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["streak"], queryFn: async () => (await api.get("/users/me/streak")).data });
  const tick = useMutation({
    mutationFn: async () => (await api.post("/users/me/streak/tick")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["streak"] }),
  });
  const current = data?.current_days ?? 0;
  const best = data?.best_days ?? 0;
  const badges = data?.badges ?? [];

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Your streak</h1>
      <div className="mt-8 grid grid-cols-2 gap-4">
        <div className="rounded-md bg-surface-elevated ring-1 ring-white/10 p-6 text-center">
          <div className="text-5xl font-black">🔥 {current}</div>
          <div className="mt-2 text-xs uppercase text-white/50">Current streak</div>
        </div>
        <div className="rounded-md bg-surface-elevated ring-1 ring-white/10 p-6 text-center">
          <div className="text-5xl font-black">🏆 {best}</div>
          <div className="mt-2 text-xs uppercase text-white/50">Best streak</div>
        </div>
      </div>
      <div className="mt-6">
        <h2 className="text-sm font-semibold text-white/70 mb-2">Badges</h2>
        <div className="flex flex-wrap gap-2">
          {["streak_7", "streak_30", "streak_100", "referral", "referrer"].map((b) => (
            <span key={b} className={`rounded-full px-3 py-1 text-xs ${badges.includes(b) ? "bg-brand text-white" : "bg-white/5 text-white/40"}`}>
              {b.replace("_", " ")}
            </span>
          ))}
        </div>
      </div>
      <Button onClick={() => tick.mutate()} className="mt-8">Log today&apos;s activity</Button>
    </div>
  );
}
