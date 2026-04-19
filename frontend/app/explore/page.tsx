"use client";

import { MoodSurface } from "@/components/mood/MoodSurface";
import { TimeBudgetSurface } from "@/components/time/TimeBudgetPicker";
import { CoViewerSurface } from "@/components/coviewer/CoViewerSurface";
import { TasteRadar } from "@/components/dna/TasteRadar";
import { NLSearchSurface } from "@/components/search/NLSearchSurface";

export default function ExplorePage() {
  return (
    <div className="space-y-10 pb-16">
      <section className="px-6 pt-8">
        <h1 className="text-3xl font-extrabold">Explore</h1>
        <p className="text-white/60">Features Netflix, Prime, HBO can&apos;t ship. Try them all.</p>
      </section>
      <section className="px-6">
        <NLSearchSurface />
      </section>
      <MoodSurface />
      <TimeBudgetSurface />
      <section className="px-6 py-6">
        <h2 className="text-lg font-semibold mb-4">Your taste DNA</h2>
        <div className="flex justify-center">
          <TasteRadar size={340} />
        </div>
      </section>
      <CoViewerSurface />
    </div>
  );
}
