"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { PosterImage } from "@/components/ui/PosterImage";
import { MatchBadge } from "@/components/content/ContentBadge";
import { useEventTracker } from "@/hooks/useEventTracker";
import { api } from "@/lib/api";
import { useRecommendations } from "@/hooks/useRecommendations";

export function RotatingHero() {
  const { data } = useRecommendations("home", 5);
  const items = data?.items ?? [];
  const [idx, setIdx] = useState(0);
  const [paused, setPaused] = useState(false);
  const { track } = useEventTracker();
  const backdropRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = backdropRef.current;
        if (!el) return;
        const y = Math.min(window.scrollY, 600);
        el.style.transform = `translate3d(0, ${y * 0.2}px, 0) scale(${1.08 + y * 0.00015})`;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => { window.removeEventListener("scroll", onScroll); cancelAnimationFrame(raf); };
  }, []);

  useEffect(() => {
    if (paused || items.length < 2) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % items.length), 8000);
    return () => clearInterval(t);
  }, [items.length, paused]);

  const featured = items[idx];
  const { data: full } = useQuery({
    queryKey: ["hero", featured?.id],
    queryFn: async () => featured ? (await api.get(`/content/${featured.id}`)).data : null,
    enabled: !!featured?.id,
  });

  return (
    <div className="relative h-[78vh] min-h-[520px] w-full overflow-hidden -mt-[60px] md:-mt-[68px]"
         onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      {/* Backdrop with parallax zoom (scroll-linked) */}
      <div ref={backdropRef} key={featured?.id}
           className="absolute inset-0 scale-[1.08] animate-[ro-fade-up_700ms_ease-out] will-change-transform">
        <PosterImage
          src={full?.backdrop_url ?? featured?.thumbnail_url}
          alt={featured?.title ?? "Featured"}
          className="h-full w-full" rounded="" variant="backdrop"
        />
      </div>

      {/* Vignettes */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/40 to-[#0a0a0b] pointer-events-none" />
      <div className="absolute inset-y-0 left-0 w-full md:w-3/5 bg-gradient-to-r from-black/90 via-black/60 to-transparent pointer-events-none" />

      <div className="absolute left-0 bottom-0 p-6 md:p-16 pt-[20vh] w-full md:max-w-3xl">
        {featured && (
          <div className="flex items-center gap-3 mb-4">
            <span className="inline-flex items-center rounded-md bg-brand px-2 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-white">
              Top Pick
            </span>
            <MatchBadge score={featured.match_score} />
          </div>
        )}
        <h1 className="text-4xl md:text-7xl font-black tracking-tight leading-[0.95] drop-shadow-[0_4px_24px_rgba(0,0,0,0.6)]">
          {featured?.title ?? "Welcome"}
        </h1>
        <div className="mt-4 flex items-center gap-3 text-xs text-white/70">
          {full?.release_year && <span className="font-semibold">{full.release_year}</span>}
          {full?.type && <span className="uppercase tracking-wider">{full.type}</span>}
          {full?.maturity_rating && <span className="rounded border border-white/40 px-1.5 py-0.5 font-bold">{full.maturity_rating}</span>}
          {full?.duration_seconds && <span>{Math.round(full.duration_seconds / 60)} min</span>}
        </div>
        <p className="mt-4 text-white/90 text-sm md:text-base line-clamp-3 max-w-xl leading-relaxed">
          {full?.description ?? featured?.reason_text ?? "Personalised picks powered by our AI recommendation engine."}
        </p>
        <div className="mt-7 flex gap-3 flex-wrap">
          {featured && (
            <Link href={`/browse/${featured.id}`} onClick={() => track("watch_intent", featured.id)}>
              <Button size="lg">▶ Play</Button>
            </Link>
          )}
          {featured && (
            <Link href={`/browse/${featured.id}`}>
              <Button variant="secondary" size="lg">ⓘ More Info</Button>
            </Link>
          )}
        </div>
        {items.length > 1 && (
          <div className="mt-6 flex gap-1.5">
            {items.map((_, i) => (
              <button key={i} onClick={() => setIdx(i)}
                aria-label={`slide ${i + 1}`}
                className={`h-1 rounded-full transition-all ${i === idx ? "w-10 bg-brand" : "w-6 bg-white/30 hover:bg-white/50"}`} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
