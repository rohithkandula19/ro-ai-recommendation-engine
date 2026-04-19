"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";

const KINDS = [
  { k: "top-raters", label: "Top Raters" },
  { k: "top-watchers", label: "Top Watchers" },
  { k: "top-reviewers", label: "Top Reviewers" },
  { k: "longest-streaks", label: "Longest Streaks" },
];

export default function LeaderboardsPage() {
  const [kind, setKind] = useState("top-raters");
  const { data } = useQuery({
    queryKey: ["lb", kind],
    queryFn: async () => (await api.get(`/leaderboards/${kind}`)).data,
  });
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Leaderboards</h1>
      <div className="mt-4 flex gap-2 flex-wrap">
        {KINDS.map((k) => (
          <button key={k.k} onClick={() => setKind(k.k)}
            className={`rounded-full px-3 py-1 text-sm ${kind === k.k ? "bg-brand" : "bg-white/10 hover:bg-white/20"}`}>
            {k.label}
          </button>
        ))}
      </div>
      <ol className="mt-6 space-y-2">
        {data?.items?.map((r: any, i: number) => (
          <li key={i} className="flex items-center gap-4 rounded-md bg-surface-elevated px-4 py-3 ring-1 ring-white/10">
            <span className="text-xl font-black text-brand w-8">#{i + 1}</span>
            <div className="flex-1">
              <div className="font-semibold">{r.display_name}</div>
              <div className="text-xs text-white/50">{r.email}</div>
            </div>
            <span className="text-lg font-bold">{r.score}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
