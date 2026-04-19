"use client";

import Link from "next/link";
import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";
import { SkeletonRow } from "@/components/ui/SkeletonCard";

export function CollectionRow({ slug, label }: { slug: string; label?: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["collection", slug],
    queryFn: async () => (await api.get(`/collections/${slug}`)).data,
  });
  const scrollRef = useRef<HTMLDivElement | null>(null);

  function scrollBy(dir: 1 | -1) {
    scrollRef.current?.scrollBy({ left: dir * (scrollRef.current.clientWidth * 0.8), behavior: "smooth" });
  }

  if (isLoading) {
    return (
      <section className="py-2">
        <h2 className="px-6 text-lg font-semibold text-white/90">{label ?? "…"}</h2>
        <SkeletonRow count={6} />
      </section>
    );
  }
  if (!data?.items?.length) return null;

  return (
    <section className="group/row py-2 relative">
      <h2 className="px-6 text-lg font-semibold text-white/90">{label ?? data.title}</h2>
      <button type="button" onClick={() => scrollBy(-1)}
        className="hidden md:block absolute left-0 top-1/2 z-10 h-28 w-10 -translate-y-1/2 rounded-r-md bg-black/60 text-2xl opacity-0 group-hover/row:opacity-100 transition">‹</button>
      <button type="button" onClick={() => scrollBy(1)}
        className="hidden md:block absolute right-0 top-1/2 z-10 h-28 w-10 -translate-y-1/2 rounded-l-md bg-black/60 text-2xl opacity-0 group-hover/row:opacity-100 transition">›</button>
      <div ref={scrollRef} className="flex gap-3 overflow-x-auto px-6 py-4 scrollbar-hide row-gradient scroll-smooth">
        {data.items.map((it: any) => (
          <Link key={it.id} href={`/browse/${it.id}`} className="min-w-[160px] w-[160px] sm:w-[180px] md:w-[200px] group">
            <PosterImage src={it.thumbnail_url} alt={it.title} className="aspect-[2/3] w-full group-hover:ring-2 group-hover:ring-brand transition" />
            <div className="mt-2 text-sm font-semibold truncate">{it.title}</div>
            <div className="text-xs text-white/50">{it.release_year}</div>
          </Link>
        ))}
      </div>
    </section>
  );
}
