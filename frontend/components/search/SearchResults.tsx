"use client";

import Link from "next/link";
import type { SearchResult } from "@/types";
import { useEventTracker } from "@/hooks/useEventTracker";

export function SearchResults({ items, query }: { items: SearchResult[]; query: string }) {
  const { track } = useEventTracker();

  if (!query.trim()) {
    return <p className="text-white/60">Type to search for movies and series.</p>;
  }
  if (items.length === 0) {
    return <p className="text-white/60">No results for &ldquo;{query}&rdquo;.</p>;
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {items.map((it) => (
        <Link
          href={`/browse/${it.id}`} key={it.id}
          onClick={() => track("click", it.id)}
          className="block"
        >
          {it.thumbnail_url ? (
            <img src={it.thumbnail_url} alt={it.title} className="aspect-video w-full rounded object-cover" />
          ) : (
            <div className="aspect-video w-full rounded bg-surface-elevated flex items-center justify-center text-sm px-2 text-center">{it.title}</div>
          )}
          <div className="mt-2 text-sm">{it.title}</div>
          <div className="text-xs text-white/50">{it.type}</div>
        </Link>
      ))}
    </div>
  );
}
