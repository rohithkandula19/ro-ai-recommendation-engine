"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRecommendations } from "@/hooks/useRecommendations";
import { SkeletonRow } from "@/components/ui/SkeletonCard";
import { ContentCard } from "./ContentCard";
import { Reveal } from "@/components/ui/Reveal";
import { useServiceFilter } from "@/hooks/useServiceFilter";

interface Props {
  surface: string;
  label: string;
  limit?: number;
}

export function ContentRow({ surface, label, limit = 20 }: Props) {
  const { data, isLoading, isError } = useRecommendations(surface, limit);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const { onlyMine, registerIds, isOnMyServices } = useServiceFilter();

  useEffect(() => {
    if (data?.items?.length) registerIds(data.items.map((it) => it.id));
  }, [data, registerIds]);

  const visibleItems = useMemo(() => {
    if (!data) return [];
    if (!onlyMine) return data.items;
    return data.items.filter((it) => isOnMyServices(it.id));
  }, [data, onlyMine, isOnMyServices]);

  function scrollBy(dir: 1 | -1) {
    scrollRef.current?.scrollBy({ left: dir * (scrollRef.current.clientWidth * 0.82), behavior: "smooth" });
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const cards = scrollRef.current?.querySelectorAll<HTMLElement>("[data-card]");
    if (!cards?.length) return;
    const active = document.activeElement as HTMLElement | null;
    const idx = Array.from(cards).findIndex((c) => c === active);
    const next = e.key === "ArrowRight" ? Math.min(cards.length - 1, idx + 1) : Math.max(0, idx - 1);
    if (next >= 0) { cards[next].focus(); e.preventDefault(); }
  }

  if (isLoading) {
    return (
      <section className="section-pad">
        <h2 className="px-6 row-heading mb-1">{label}</h2>
        <SkeletonRow count={6} />
      </section>
    );
  }

  if (isError) return null;
  if (!data || data.items.length === 0) {
    return (
      <section className="section-pad">
        <h2 className="px-6 row-heading mb-1">{label}</h2>
        <div className="px-6 py-4 text-sm text-white/50">Nothing here yet — keep watching to get picks.</div>
      </section>
    );
  }
  if (onlyMine && visibleItems.length === 0) {
    return (
      <section className="section-pad">
        <h2 className="px-6 row-heading mb-1">{label}</h2>
        <div className="px-6 py-4 text-sm text-white/50">Nothing in this row is available on your services. Toggle off the filter to see all picks.</div>
      </section>
    );
  }

  return (
    <Reveal as="section" className="group/row section-pad relative">
      <h2 className="px-6 row-heading mb-1">{label}</h2>
      <button type="button" aria-label="scroll left" onClick={() => scrollBy(-1)}
        className="hidden md:flex absolute left-0 top-1/2 z-10 h-28 w-12 -translate-y-1/2 items-center justify-center
                   bg-gradient-to-r from-black via-black/60 to-transparent
                   text-4xl text-white/80 hover:text-white opacity-0 group-hover/row:opacity-100 transition-opacity">‹</button>
      <button type="button" aria-label="scroll right" onClick={() => scrollBy(1)}
        className="hidden md:flex absolute right-0 top-1/2 z-10 h-28 w-12 -translate-y-1/2 items-center justify-center
                   bg-gradient-to-l from-black via-black/60 to-transparent
                   text-4xl text-white/80 hover:text-white opacity-0 group-hover/row:opacity-100 transition-opacity">›</button>
      <div ref={scrollRef} onKeyDown={onKeyDown}
        className="flex gap-3 overflow-x-auto px-6 pt-3 pb-6 scrollbar-hide row-gradient scroll-smooth snap-row">
        {visibleItems.map((it) => (
          <ContentCard key={it.id} item={it} surface={surface} />
        ))}
      </div>
    </Reveal>
  );
}
