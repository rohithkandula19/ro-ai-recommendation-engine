"use client";

import { useState } from "react";
import { useCoViewer } from "@/hooks/useUniqueFeatures";
import { ContentCard } from "@/components/home/ContentCard";
import { SkeletonRow } from "@/components/ui/SkeletonCard";
import { Button } from "@/components/ui/Button";

export function CoViewerSurface() {
  const [input, setInput] = useState("");
  const [ids, setIds] = useState<string[]>([]);
  const { data, isLoading } = useCoViewer(ids, 12);

  function addId() {
    const v = input.trim();
    if (v && !ids.includes(v) && /^[0-9a-f-]{36}$/i.test(v)) {
      setIds([...ids, v]);
      setInput("");
    }
  }

  return (
    <section className="px-6 py-6">
      <h2 className="text-lg font-semibold">Watch with someone</h2>
      <p className="text-xs text-white/60 mb-3">
        Add another user&apos;s ID — we blend your taste DNAs and find the overlap.
      </p>
      <div className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
               placeholder="user-id (UUID)"
               className="w-72 rounded bg-black/60 ring-1 ring-white/10 px-3 py-1.5 text-sm" />
        <Button onClick={addId}>Add</Button>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {ids.map((i) => (
          <span key={i} className="rounded-full bg-white/10 px-3 py-0.5 text-xs">
            {i.slice(0, 8)}… <button onClick={() => setIds(ids.filter((x) => x !== i))} className="ml-1">×</button>
          </span>
        ))}
      </div>
      <div className="mt-6">
        {isLoading ? <SkeletonRow count={6} /> : (
          <div className="flex gap-3 overflow-x-auto scrollbar-hide py-2">
            {data?.items?.map((it: any) => <ContentCard key={it.id} item={it} />)}
          </div>
        )}
      </div>
    </section>
  );
}
