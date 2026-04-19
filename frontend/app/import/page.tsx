"use client";

import { useState } from "react";
import { api, getAccessToken } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export default function ImportPage() {
  const [source, setSource] = useState<"letterboxd" | "trakt">("letterboxd");
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const token = getAccessToken();
      const r = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") +
        `/imports/csv?source=${source}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      setResult(await r.json());
    } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Import watch history</h1>
      <p className="text-sm text-white/60 mt-2">Upload a Letterboxd diary.csv or Trakt export.csv — we match titles to our catalog.</p>
      <div className="mt-6 flex gap-2">
        <Button variant={source === "letterboxd" ? "primary" : "secondary"} onClick={() => setSource("letterboxd")}>Letterboxd</Button>
        <Button variant={source === "trakt" ? "primary" : "secondary"} onClick={() => setSource("trakt")}>Trakt</Button>
      </div>
      <input type="file" accept=".csv" onChange={onUpload} disabled={busy}
        className="mt-6 block w-full text-sm text-white/80 file:bg-brand file:text-white file:rounded-md file:border-0 file:px-4 file:py-2 file:mr-4" />
      {result && (
        <pre className="mt-6 rounded-md bg-surface-elevated p-4 text-xs">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
