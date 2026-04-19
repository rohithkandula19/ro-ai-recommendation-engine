"use client";

import { useState } from "react";
import { useTimeBudget } from "@/hooks/useUniqueFeatures";
import { ContentCard } from "@/components/home/ContentCard";
import { SkeletonRow } from "@/components/ui/SkeletonCard";
import { Button } from "@/components/ui/Button";

const PRESETS = [15, 30, 45, 60, 90, 120];

export function TimeBudgetSurface() {
  const [minutes, setMinutes] = useState(45);
  const { data, isLoading } = useTimeBudget(minutes, 12);

  return (
    <section className="px-6 py-6">
      <div className="flex items-baseline gap-3">
        <h2 className="text-lg font-semibold">I have</h2>
        <input type="number" min={5} max={480}
               className="w-20 rounded bg-black/60 ring-1 ring-white/10 px-2 py-1 text-center"
               value={minutes} onChange={(e) => setMinutes(Number(e.target.value) || 0)} />
        <span className="text-sm text-white/70">minutes</span>
      </div>
      <div className="mt-2 flex gap-2 flex-wrap">
        {PRESETS.map((m) => (
          <Button key={m} variant={minutes === m ? "primary" : "secondary"} onClick={() => setMinutes(m)}>
            {m}m
          </Button>
        ))}
      </div>
      <div className="mt-4">
        {isLoading ? <SkeletonRow count={6} /> : (
          <div className="flex gap-3 overflow-x-auto scrollbar-hide py-2">
            {data?.items?.map((it: any) => <ContentCard key={it.id} item={it} />)}
          </div>
        )}
      </div>
    </section>
  );
}
