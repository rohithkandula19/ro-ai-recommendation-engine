"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { PosterImage } from "@/components/ui/PosterImage";
import { api } from "@/lib/api";
import { useRecommendations } from "@/hooks/useRecommendations";

export function RotatingHero() {
  const { data } = useRecommendations("home", 5);
  const items = data?.items ?? [];
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (items.length < 2) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % items.length), 8000);
    return () => clearInterval(t);
  }, [items.length]);

  const featured = items[idx];
  const { data: full } = useQuery({
    queryKey: ["hero", featured?.id],
    queryFn: async () => featured ? (await api.get(`/content/${featured.id}`)).data : null,
    enabled: !!featured?.id,
  });

  return (
    <div className="relative h-[72vh] min-h-[460px] w-full overflow-hidden">
      <div key={featured?.id} className="absolute inset-0 transition-opacity duration-700">
        <PosterImage src={featured?.thumbnail_url} alt={featured?.title ?? "Featured"} className="h-full w-full" rounded="" />
      </div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/40 to-black pointer-events-none" />
      <div className="absolute inset-y-0 left-0 w-full md:w-3/5 bg-gradient-to-r from-black/85 via-black/55 to-transparent pointer-events-none" />
      <div className="absolute left-0 bottom-0 p-8 md:p-14 max-w-2xl">
        {featured && (
          <span className="inline-flex items-center gap-2 rounded bg-brand/90 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider">
            Featured · {idx + 1}/{items.length} · {Math.round(featured.match_score * 100)}%
          </span>
        )}
        <h1 className="mt-3 text-3xl md:text-6xl font-extrabold tracking-tight drop-shadow-lg">
          {featured?.title ?? "Welcome"}
        </h1>
        <p className="mt-3 text-white/85 text-sm md:text-base line-clamp-3 max-w-xl">
          {full?.description ?? featured?.reason_text ?? "Personalised picks powered by our AI recommendation engine."}
        </p>
        <div className="mt-6 flex gap-3">
          {featured && <Link href={`/watch/${featured.id}`}><Button>▶ Play</Button></Link>}
          {featured && <Link href={`/browse/${featured.id}`}><Button variant="secondary">ℹ More info</Button></Link>}
        </div>
        <div className="mt-4 flex gap-1">
          {items.map((_, i) => (
            <span key={i} className={`h-1 w-8 rounded-full transition ${i === idx ? "bg-brand" : "bg-white/20"}`} />
          ))}
        </div>
      </div>
    </div>
  );
}
