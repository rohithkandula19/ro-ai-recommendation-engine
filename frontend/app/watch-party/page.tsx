"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export default function WatchPartyPage() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [contentId, setContentId] = useState("");
  const [created, setCreated] = useState<string | null>(null);

  async function create() {
    const r = await api.post("/watch-parties", { content_id: contentId });
    setCreated(r.data.room_code);
  }

  async function join() {
    const r = await api.get(`/watch-parties/${code.trim().toUpperCase()}`);
    if (r.data) router.push(`/watch-party/${r.data.room_code}?content=${r.data.content_id}`);
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10 space-y-8">
      <h1 className="text-3xl font-extrabold">Watch Party</h1>

      <section className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-5">
        <h2 className="text-lg font-semibold mb-3">Host a party</h2>
        <input value={contentId} onChange={(e) => setContentId(e.target.value)}
          placeholder="content UUID to watch"
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <Button onClick={create} className="mt-3" disabled={!contentId.trim()}>Create room</Button>
        {created && (
          <p className="mt-4 text-sm">Room code: <code className="text-brand font-bold">{created}</code> — share with friends</p>
        )}
      </section>

      <section className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-5">
        <h2 className="text-lg font-semibold mb-3">Join a party</h2>
        <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="Room code (e.g. A1B2C3)"
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10 uppercase" />
        <Button onClick={join} className="mt-3" disabled={!code.trim()}>Join</Button>
      </section>
    </div>
  );
}
