"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Ach { key: string; label: string; emoji: string; desc: string; unlocked: boolean }

export default function AchievementsPage() {
  const { data } = useQuery<{ items: Ach[]; progress: string }>({
    queryKey: ["achievements"],
    queryFn: async () => (await api.get("/achievements")).data,
  });
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold">Skill Tree</h1>
        <span className="text-brand font-bold">{data?.progress ?? "…"}</span>
      </div>
      <p className="text-sm text-white/60 mt-1">Unlock as you watch, rate, review, and take chances.</p>
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3">
        {data?.items.map((a) => (
          <div key={a.key} className={`rounded-md p-4 ring-1 ring-white/10 flex gap-4 items-center
            ${a.unlocked ? "bg-gradient-to-br from-brand/20 to-transparent" : "bg-surface-elevated opacity-60"}`}>
            <div className={`text-4xl ${a.unlocked ? "" : "grayscale"}`}>{a.emoji}</div>
            <div>
              <div className="font-semibold">{a.label}</div>
              <div className="text-xs text-white/60">{a.desc}</div>
              {a.unlocked && <div className="text-[10px] uppercase tracking-wider text-brand mt-1">Unlocked</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
