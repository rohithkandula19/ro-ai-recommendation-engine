"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { useNLSearch } from "@/hooks/useUniqueFeatures";

const EXAMPLES = [
  "something dark and funny from the 90s",
  "feel-good under 90 minutes",
  "tense thriller I can finish tonight",
  "thoughtful sci-fi that's not too long",
];

export function NLSearchSurface() {
  const [q, setQ] = useState("");
  const mut = useNLSearch();

  async function submit() {
    if (q.trim()) await mut.mutateAsync(q);
  }

  return (
    <div>
      <h2 className="text-lg font-semibold">Ask the engine</h2>
      <p className="text-xs text-white/60 mb-3">Say what you want in your own words. AI parses → structured filters.</p>
      <div className="flex gap-2">
        <input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="e.g. something dark and funny from the 90s"
          className="flex-1 rounded-md bg-black/60 px-4 py-2.5 ring-1 ring-white/10 focus:ring-white/30 outline-none"
          onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
        />
        <Button onClick={submit} disabled={mut.isPending}>
          {mut.isPending ? "…" : "Ask"}
        </Button>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button key={ex} type="button" onClick={() => setQ(ex)}
            className="rounded-full bg-white/5 px-3 py-1 text-xs text-white/60 hover:bg-white/10">
            {ex}
          </button>
        ))}
      </div>
      {mut.data && (
        <div className="mt-5">
          {Object.keys(mut.data.parsed_filters || {}).length > 0 && (
            <div className="mb-3 text-xs text-white/60">
              AI parsed: <code className="text-white/80">{JSON.stringify(mut.data.parsed_filters)}</code>
            </div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {mut.data.results?.map((r: any) => (
              <Link key={r.id} href={`/browse/${r.id}`} className="block">
                {r.thumbnail_url
                  ? <img src={r.thumbnail_url} alt={r.title} className="aspect-video w-full rounded object-cover" />
                  : <div className="aspect-video w-full rounded bg-surface-elevated flex items-center justify-center text-sm px-2 text-center">{r.title}</div>
                }
                <div className="mt-1 text-sm truncate">{r.title}</div>
                <div className="text-[10px] text-white/50">{r.release_year} · {r.type}</div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
