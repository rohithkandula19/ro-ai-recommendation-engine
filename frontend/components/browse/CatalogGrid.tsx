"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";
import { Button } from "@/components/ui/Button";
import type { Genre } from "@/types";

interface Item {
  id: string; title: string; type: string;
  release_year: number | null; duration_seconds: number | null;
  thumbnail_url: string | null;
  popularity_score: number; completion_rate: number;
  maturity_rating: string | null; genre_ids: number[];
}

interface Filters {
  genre: number | null;
  min_year: number | null;
  max_year: number | null;
  max_minutes: number | null;
  sort: "popular" | "newest" | "oldest" | "title" | "completion";
}

export function CatalogGrid({ endpoint, title, showRuntime }: { endpoint: "/movies" | "/series"; title: string; showRuntime?: boolean }) {
  const [filters, setFilters] = useState<Filters>({ genre: null, min_year: null, max_year: null, max_minutes: null, sort: "popular" });
  const [limit, setLimit] = useState(40);

  const { data: genres } = useQuery<Genre[]>({
    queryKey: ["genres"],
    queryFn: async () => (await api.get("/content/genres")).data,
  });
  const { data, isLoading } = useQuery<{ total: number; items: Item[] }>({
    queryKey: ["catalog", endpoint, filters, limit],
    queryFn: async () => (await api.get(endpoint, { params: { ...filters, limit, offset: 0 } })).data,
  });

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <h1 className="text-3xl font-extrabold">{title}</h1>
        <div className="text-xs text-white/50">{data?.total?.toLocaleString() ?? "…"} titles</div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <select value={filters.sort} onChange={(e) => setFilters({ ...filters, sort: e.target.value as Filters["sort"] })}
          className="rounded-md bg-black/60 px-3 py-1.5 text-sm ring-1 ring-white/10">
          <option value="popular">Most popular</option>
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="title">A → Z</option>
          <option value="completion">Highest finish rate</option>
        </select>

        <select value={filters.genre ?? ""} onChange={(e) => setFilters({ ...filters, genre: e.target.value ? Number(e.target.value) : null })}
          className="rounded-md bg-black/60 px-3 py-1.5 text-sm ring-1 ring-white/10">
          <option value="">All genres</option>
          {genres?.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>

        <input type="number" placeholder="From year" value={filters.min_year ?? ""}
          onChange={(e) => setFilters({ ...filters, min_year: e.target.value ? Number(e.target.value) : null })}
          className="w-28 rounded-md bg-black/60 px-3 py-1.5 text-sm ring-1 ring-white/10" />
        <input type="number" placeholder="To year" value={filters.max_year ?? ""}
          onChange={(e) => setFilters({ ...filters, max_year: e.target.value ? Number(e.target.value) : null })}
          className="w-28 rounded-md bg-black/60 px-3 py-1.5 text-sm ring-1 ring-white/10" />
        {showRuntime && (
          <input type="number" placeholder="Max minutes" value={filters.max_minutes ?? ""}
            onChange={(e) => setFilters({ ...filters, max_minutes: e.target.value ? Number(e.target.value) : null })}
            className="w-32 rounded-md bg-black/60 px-3 py-1.5 text-sm ring-1 ring-white/10" />
        )}

        {(filters.genre || filters.min_year || filters.max_year || filters.max_minutes) && (
          <button onClick={() => setFilters({ genre: null, min_year: null, max_year: null, max_minutes: null, sort: filters.sort })}
            className="rounded-md bg-white/10 px-3 py-1.5 text-sm hover:bg-white/20">Clear</button>
        )}
      </div>

      {isLoading ? (
        <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Array.from({ length: 18 }).map((_, i) => (
            <div key={i} className="aspect-[2/3] rounded-md bg-surface-elevated animate-pulse" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <>
          <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {data.items.map((it) => (
              <Link key={it.id} href={`/browse/${it.id}`} className="block group">
                <PosterImage src={it.thumbnail_url} alt={it.title} className="aspect-[2/3] w-full group-hover:ring-2 group-hover:ring-brand transition" />
                <div className="mt-2">
                  <div className="text-sm font-semibold truncate">{it.title}</div>
                  <div className="text-xs text-white/50 flex gap-2">
                    {it.release_year && <span>{it.release_year}</span>}
                    {it.duration_seconds && <span>· {Math.round(it.duration_seconds / 60)} min</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {data.items.length < data.total && (
            <div className="mt-8 text-center">
              <Button onClick={() => setLimit(limit + 40)}>Load more</Button>
            </div>
          )}
        </>
      ) : (
        <p className="mt-8 text-white/60">No titles match those filters.</p>
      )}
    </div>
  );
}
