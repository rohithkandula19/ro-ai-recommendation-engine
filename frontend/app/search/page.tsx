"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { NLSearchSurface } from "@/components/search/NLSearchSurface";
import { useSearch } from "@/hooks/useSearch";
import { useEventTracker } from "@/hooks/useEventTracker";

function SearchInner() {
  const sp = useSearchParams();
  const initial = sp?.get("q") ?? "";
  const [q, setQ] = useState(initial);
  const [mode, setMode] = useState<"title" | "ai">("title");
  const { data } = useSearch(q);
  const { track } = useEventTracker();

  useEffect(() => {
    const trimmed = q.trim();
    if (trimmed) track("search", null, trimmed.length);
  }, [q, track]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="text-2xl font-bold mb-4">Search</h1>
      <div className="flex gap-2 mb-4">
        <button onClick={() => setMode("title")}
          className={`rounded-md px-3 py-1 text-sm ${mode === "title" ? "bg-brand text-white" : "bg-white/10 text-white/70"}`}>Title</button>
        <button onClick={() => setMode("ai")}
          className={`rounded-md px-3 py-1 text-sm ${mode === "ai" ? "bg-brand text-white" : "bg-white/10 text-white/70"}`}>AI · natural language</button>
      </div>
      {mode === "title" ? (
        <>
          <SearchBar value={q} onChange={setQ} placeholder="Search by title, description..." />
          <div className="mt-8">
            <SearchResults query={q} items={data?.results ?? []} />
          </div>
        </>
      ) : (
        <NLSearchSurface />
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-8 text-white/60">Loading…</div>}>
      <SearchInner />
    </Suspense>
  );
}
