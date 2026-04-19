"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";
import { Button } from "@/components/ui/Button";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [genres, setGenres] = useState<number[]>([]);
  const [ratings, setRatings] = useState<Record<string, number>>({});

  const { data: genreList } = useQuery<any[]>({
    queryKey: ["genres-ob"],
    queryFn: async () => (await api.get("/content/genres")).data,
  });
  const { data: picks } = useQuery<any[]>({
    queryKey: ["ob-picks"],
    queryFn: async () => (await api.get("/content?limit=12")).data,
    enabled: step === 2,
  });

  async function finish() {
    if (genres.length) {
      await api.put("/users/me/preferences", {
        genre_ids: genres, preferred_language: "en", maturity_rating: "R", onboarding_complete: true,
      }).catch(() => {});
    }
    for (const [cid, r] of Object.entries(ratings)) {
      await api.post(`/users/me/ratings/${cid}`, { rating: r }).catch(() => {});
    }
    router.push("/browse");
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-2xl space-y-6">
        <div className="flex gap-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`h-1 flex-1 rounded ${s <= step ? "bg-brand" : "bg-white/10"}`} />
          ))}
        </div>

        {step === 1 && (
          <div>
            <h1 className="text-3xl font-extrabold">Welcome to RO.</h1>
            <p className="mt-2 text-white/70">Pick your favorite genres — we&apos;ll start there.</p>
            <div className="mt-6 flex flex-wrap gap-2">
              {genreList?.slice(0, 30).map((g) => (
                <button key={g.id} onClick={() => setGenres((v) => v.includes(g.id) ? v.filter(x => x !== g.id) : [...v, g.id])}
                  className={`rounded-full px-4 py-2 text-sm ${genres.includes(g.id) ? "bg-brand text-white" : "bg-white/10 hover:bg-white/20"}`}>
                  {g.name}
                </button>
              ))}
            </div>
            <div className="mt-8 flex justify-between">
              <button onClick={() => router.push("/browse")} className="text-sm text-white/50">Skip</button>
              <Button onClick={() => setStep(2)} disabled={genres.length === 0}>Next · pick 5 favorites</Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-3xl font-extrabold">Rate a few titles</h1>
            <p className="mt-2 text-white/70">More stars = better calibration. Skip what you haven&apos;t seen.</p>
            <div className="mt-6 grid grid-cols-3 sm:grid-cols-4 gap-3">
              {picks?.map((c: any) => (
                <div key={c.id} className="space-y-2">
                  <PosterImage src={c.thumbnail_url} alt={c.title} className="aspect-[2/3] w-full" />
                  <div className="text-xs truncate">{c.title}</div>
                  <div className="flex gap-0.5">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button key={n} onClick={() => setRatings((r) => ({ ...r, [c.id]: n }))}
                        className={`text-sm ${(ratings[c.id] ?? 0) >= n ? "text-yellow-400" : "text-white/20"}`}>★</button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 flex justify-between">
              <button onClick={() => setStep(1)} className="text-sm text-white/50">Back</button>
              <Button onClick={() => setStep(3)}>Next</Button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="text-center">
            <h1 className="text-3xl font-extrabold">All set.</h1>
            <p className="mt-3 text-white/70">
              We&apos;ll learn from every click, watch, and rating. Come back tomorrow and see your DNA shift.
            </p>
            <div className="mt-8 grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-3xl">🧬</div>
                <div className="mt-1 text-xs text-white/60">Taste DNA</div>
              </div>
              <div>
                <div className="text-3xl">🎭</div>
                <div className="mt-1 text-xs text-white/60">Mood dial</div>
              </div>
              <div>
                <div className="text-3xl">💬</div>
                <div className="mt-1 text-xs text-white/60">Ask RO</div>
              </div>
            </div>
            <Button onClick={finish} className="mt-10">Enter the app →</Button>
          </div>
        )}
      </div>
    </div>
  );
}
