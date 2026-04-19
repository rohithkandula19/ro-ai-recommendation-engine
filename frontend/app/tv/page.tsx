"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRecommendations } from "@/hooks/useRecommendations";
import { PosterImage } from "@/components/ui/PosterImage";

/**
 * 10-foot UI: large cards, D-pad keyboard navigation (arrows + Enter),
 * minimal chrome. Designed for Apple TV / Android TV / Chromecast browsers.
 */
export default function TVUI() {
  const { data: home } = useRecommendations("home", 12);
  const { data: trending } = useRecommendations("trending", 12);
  const [focus, setFocus] = useState<{ row: number; col: number }>({ row: 0, col: 0 });
  const rowRefs = useRef<(HTMLDivElement | null)[]>([]);

  const rows = [home, trending];

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight") setFocus((f) => ({ ...f, col: f.col + 1 }));
      else if (e.key === "ArrowLeft") setFocus((f) => ({ ...f, col: Math.max(0, f.col - 1) }));
      else if (e.key === "ArrowDown") setFocus((f) => ({ row: Math.min(rows.length - 1, f.row + 1), col: 0 }));
      else if (e.key === "ArrowUp") setFocus((f) => ({ row: Math.max(0, f.row - 1), col: 0 }));
      else if (e.key === "Enter") {
        const row = rows[focus.row];
        const item = row?.items?.[focus.col];
        if (item) window.location.href = `/browse/${item.id}`;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [rows, focus]);

  useEffect(() => {
    const el = rowRefs.current[focus.row];
    const card = el?.children[focus.col] as HTMLElement | undefined;
    card?.scrollIntoView({ behavior: "smooth", inline: "center", block: "center" });
  }, [focus]);

  return (
    <div className="min-h-screen bg-black">
      <div className="px-12 py-8">
        <div className="text-4xl font-black text-brand">RO · TV</div>
        <div className="text-sm text-white/50">Use arrow keys / remote D-pad to navigate · Enter to open</div>
      </div>
      {[
        { label: "For You", data: home },
        { label: "Trending", data: trending },
      ].map((row, rIdx) => (
        <section key={row.label} className="mb-10">
          <h2 className="px-12 text-3xl font-bold mb-4">{row.label}</h2>
          <div ref={(el) => { rowRefs.current[rIdx] = el; }}
            className="flex gap-6 overflow-x-auto scrollbar-hide px-12">
            {row.data?.items?.map((it, cIdx) => {
              const focused = focus.row === rIdx && focus.col === cIdx;
              return (
                <Link key={it.id} href={`/browse/${it.id}`}
                  className={`min-w-[280px] w-[280px] transition-all ${focused ? "scale-110 ring-4 ring-brand" : "scale-100"}`}>
                  <PosterImage src={it.thumbnail_url} alt={it.title} className="aspect-[2/3] w-full" />
                  <div className="mt-3 text-xl font-bold truncate">{it.title}</div>
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
