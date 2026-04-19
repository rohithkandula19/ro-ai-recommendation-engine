"use client";

import { useState } from "react";
import { MoodDial } from "./MoodDial";
import { useMoodRecs } from "@/hooks/useUniqueFeatures";
import { ContentCard } from "@/components/home/ContentCard";
import { SkeletonRow } from "@/components/ui/SkeletonCard";

export function MoodSurface() {
  const [mood, setMood] = useState({ chill_tense: 0.5, light_thoughtful: 0.5 });
  const { data, isLoading } = useMoodRecs(mood.chill_tense, mood.light_thoughtful, 12);

  return (
    <section className="px-6 py-6">
      <div className="flex flex-col md:flex-row gap-6 items-start">
        <div>
          <h2 className="text-lg font-semibold">How do you feel right now?</h2>
          <p className="text-xs text-white/60 mb-3">Drag inside the pad. We&apos;ll reshape the recs.</p>
          <MoodDial value={mood} onChange={setMood} />
        </div>
        <div className="flex-1 w-full">
          {isLoading ? (
            <SkeletonRow count={6} />
          ) : (
            <div className="flex gap-3 overflow-x-auto scrollbar-hide py-2">
              {data?.items?.map((it: any) => <ContentCard key={it.id} item={it} />)}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
