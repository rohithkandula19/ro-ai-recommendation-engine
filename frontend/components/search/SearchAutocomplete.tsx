"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Item { id: string; title: string; type: string; release_year: number | null; thumbnail_url: string | null; sim: number }

export function SearchAutocomplete() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(-1);
  const router = useRouter();
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const { data } = useQuery<{ items: Item[] }>({
    queryKey: ["suggest", q],
    queryFn: async () => (await api.get(`/search/suggest?q=${encodeURIComponent(q)}`)).data,
    enabled: q.trim().length >= 2,
    staleTime: 60_000,
  });

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    const items = data?.items || [];
    if (e.key === "ArrowDown") { e.preventDefault(); setFocused((i) => Math.min(items.length - 1, i + 1)); setOpen(true); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setFocused((i) => Math.max(-1, i - 1)); }
    else if (e.key === "Enter") {
      e.preventDefault();
      if (focused >= 0 && items[focused]) router.push(`/browse/${items[focused].id}`);
      else if (q.trim()) router.push(`/search?q=${encodeURIComponent(q.trim())}`);
      setOpen(false);
    } else if (e.key === "Escape") setOpen(false);
  }

  return (
    <div ref={ref} className="relative">
      <input value={q} onChange={(e) => { setQ(e.target.value); setOpen(true); setFocused(-1); }}
        onFocus={() => setOpen(true)} onKeyDown={onKey}
        placeholder="Search titles…"
        className="w-64 rounded-md bg-black/60 px-3 py-1.5 text-sm outline-none ring-1 ring-white/10 focus:ring-white/30" />
      {open && q.trim().length >= 2 && (data?.items?.length ?? 0) > 0 && (
        <div className="absolute right-0 mt-2 w-80 rounded-md bg-surface-elevated ring-1 ring-white/10 shadow-xl overflow-hidden">
          {data!.items.map((it, i) => (
            <Link key={it.id} href={`/browse/${it.id}`} onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-3 py-2 text-sm ${focused === i ? "bg-white/10" : "hover:bg-white/5"}`}>
              {it.thumbnail_url ? (
                <img src={it.thumbnail_url} alt="" className="h-10 w-7 rounded object-cover" />
              ) : <div className="h-10 w-7 rounded bg-white/10" />}
              <div className="flex-1 min-w-0">
                <div className="truncate">{highlight(it.title, q)}</div>
                <div className="text-xs text-white/50">{it.release_year} · {it.type}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function highlight(title: string, q: string) {
  const i = title.toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return <>{title}</>;
  return <>
    {title.slice(0, i)}
    <span className="text-brand font-semibold">{title.slice(i, i + q.length)}</span>
    {title.slice(i + q.length)}
  </>;
}
