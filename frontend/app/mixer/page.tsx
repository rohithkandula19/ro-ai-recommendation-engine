"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { PosterImage } from "@/components/ui/PosterImage";

export default function MixerPage() {
  const [other, setOther] = useState("");
  const [data, setData] = useState<any>(null);
  async function mix() {
    const r = await api.post("/mixer", { other_user_id: other.trim(), limit: 12 });
    setData(r.data);
  }
  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">RO Mixer</h1>
      <p className="text-sm text-white/60 mt-1">Pair two people&apos;s DNA. We find the overlap zone — the picks you&apos;ll both love.</p>

      <div className="mt-6 rounded-md bg-surface-elevated p-4 ring-1 ring-white/10 space-y-3">
        <input value={other} onChange={(e) => setOther(e.target.value)}
          placeholder="friend's user UUID"
          className="w-full rounded bg-black/60 px-3 py-2 ring-1 ring-white/10 font-mono text-sm" />
        <Button onClick={mix} disabled={!other}>Mix</Button>
      </div>

      {data?.items && (
        <>
          <p className="mt-6 text-sm text-white/60">Blending with <span className="font-semibold text-white">{data.other.display_name}</span></p>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {data.items.map((it: any) => (
              <Link href={`/browse/${it.id}`} key={it.id} className="group">
                <PosterImage src={it.thumbnail_url} alt={it.title} className="aspect-[2/3] w-full group-hover:ring-2 group-hover:ring-brand transition" />
                <div className="mt-2 text-sm truncate">{it.title}</div>
                <div className="text-xs text-brand">{Math.round(it.match * 100)}% shared match</div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
