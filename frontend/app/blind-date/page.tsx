"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { PosterImage } from "@/components/ui/PosterImage";

export default function BlindDatePage() {
  const [bd, setBd] = useState<any>(null);
  const [revealed, setRevealed] = useState<any>(null);
  const [rating, setRating] = useState(0);
  const [phase, setPhase] = useState<"idle" | "blind" | "revealed" | "rated">("idle");

  async function start() {
    const r = await api.post("/blind-date/start");
    setBd(r.data); setPhase("blind"); setRevealed(null);
  }
  async function reveal() {
    const r = await api.post(`/blind-date/${bd.blind_date_id}/reveal`);
    setRevealed(r.data); setPhase("revealed");
  }
  async function rate(n: number) {
    setRating(n);
    await api.post(`/blind-date/${bd.blind_date_id}/rate`, { rating: n });
    setPhase("rated");
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-16 text-center space-y-8">
      <h1 className="text-4xl font-extrabold">Blind Date</h1>
      <p className="text-white/60">We pick. You don&apos;t see what it is until after you&apos;ve watched it.</p>

      {phase === "idle" && <Button onClick={start} className="text-base px-8 py-3">Start a Blind Date</Button>}

      {phase === "blind" && bd && (
        <div className="rounded-2xl bg-surface-elevated ring-1 ring-white/10 p-10 space-y-4">
          <div className="text-7xl">🎭</div>
          <p className="text-xl font-bold">{bd.hint}</p>
          <p className="text-sm text-white/50">Watch it tonight. Come back and reveal.</p>
          <Button onClick={reveal} variant="secondary">Reveal now</Button>
        </div>
      )}

      {phase === "revealed" && revealed && (
        <div className="space-y-4">
          <div className="inline-block">
            <PosterImage src={revealed.thumbnail_url} alt={revealed.title} className="w-60 aspect-[2/3] mx-auto" />
          </div>
          <h2 className="text-3xl font-extrabold">{revealed.title}</h2>
          <p className="text-white/70 text-sm max-w-lg mx-auto">{revealed.description}</p>
          <p className="text-sm text-white/60 mt-6">How was it?</p>
          <div className="flex justify-center gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} onClick={() => rate(n)}
                className={`text-3xl ${n <= rating ? "text-yellow-400" : "text-white/20"}`}>★</button>
            ))}
          </div>
        </div>
      )}

      {phase === "rated" && <p className="text-lg">Thanks for trusting us. 🍿</p>}
    </div>
  );
}
