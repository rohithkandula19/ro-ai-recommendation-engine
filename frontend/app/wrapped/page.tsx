"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";

export default function WrappedPage() {
  const year = new Date().getFullYear();
  const { data } = useQuery({
    queryKey: ["wrapped", year],
    queryFn: async () => (await api.get(`/wrapped/${year}`)).data,
  });

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 -z-10">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(229,9,20,0.35), transparent 60%)" }} />
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(59,130,246,0.25), transparent 60%)" }} />
      </div>
      <div className="mx-auto max-w-3xl px-6 py-20 space-y-16 text-center">
        <section>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">RO Wrapped</p>
          <h1 className="mt-2 text-6xl md:text-8xl font-black">{year}</h1>
        </section>

        <section className="rounded-2xl bg-white/5 ring-1 ring-white/10 p-10">
          <p className="text-sm text-white/60">You watched</p>
          <p className="mt-2 text-7xl font-black text-brand">{data?.total_watched ?? "…"}</p>
          <p className="mt-2 text-white/60">{data?.completed ?? 0} to the credits</p>
        </section>

        {data?.top_genre && (
          <section>
            <p className="text-xs uppercase tracking-wider text-white/50">Your top genre</p>
            <p className="mt-2 text-5xl font-black">{data.top_genre}</p>
          </section>
        )}

        {data?.top_axis && (
          <section>
            <p className="text-xs uppercase tracking-wider text-white/50">Your viewing personality</p>
            <p className="mt-2 text-3xl font-black capitalize">{data.top_axis}-driven viewer</p>
            <p className="mt-2 text-white/60 text-sm">Your DNA leans hardest on {data.top_axis} — {Math.round(data.dna?.[data.top_axis] * 100)}%.</p>
          </section>
        )}

        {data?.spotlight?.length > 0 && (
          <section>
            <p className="text-xs uppercase tracking-wider text-white/50">Some highlights</p>
            <div className="mt-6 grid grid-cols-3 md:grid-cols-6 gap-3">
              {data.spotlight.map((s: any, i: number) => (
                <PosterImage key={i} src={s.thumbnail_url} alt={s.title} className="aspect-[2/3] w-full" />
              ))}
            </div>
          </section>
        )}

        {data?.first_watch && data?.last_watch && (
          <section className="grid md:grid-cols-2 gap-4">
            <div className="rounded-xl bg-white/5 p-6">
              <p className="text-xs uppercase text-white/50">First watch</p>
              <p className="mt-2 text-xl font-bold">{data.first_watch}</p>
            </div>
            <div className="rounded-xl bg-white/5 p-6">
              <p className="text-xs uppercase text-white/50">Most recent</p>
              <p className="mt-2 text-xl font-bold">{data.last_watch}</p>
            </div>
          </section>
        )}

        <p className="text-xs text-white/40">Share — or check back next year.</p>
      </div>
    </div>
  );
}
