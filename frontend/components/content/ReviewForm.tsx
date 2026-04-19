"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

export function ReviewForm({ contentId }: { contentId: string }) {
  const [body, setBody] = useState("");
  const [hasSpoilers, setHasSpoilers] = useState(false);
  const [busy, setBusy] = useState(false);
  const qc = useQueryClient();
  const toast = useToast();

  async function submit() {
    if (body.trim().length < 10) return;
    setBusy(true);
    try {
      await api.post("/reviews/write", { content_id: contentId, body, has_spoilers: hasSpoilers });
      toast.show("Review posted", "success");
      setBody("");
      setHasSpoilers(false);
      qc.invalidateQueries({ queryKey: ["reviews", contentId] });
    } finally { setBusy(false); }
  }

  return (
    <div className="mt-4 rounded-md bg-surface-elevated ring-1 ring-white/10 p-3 space-y-2">
      <textarea value={body} onChange={(e) => setBody(e.target.value)}
        rows={3} placeholder="Share your thoughts (min 10 chars)…"
        className="w-full rounded bg-black/60 px-3 py-2 text-sm ring-1 ring-white/10" />
      <label className="flex items-center gap-2 text-xs text-white/70">
        <input type="checkbox" checked={hasSpoilers} onChange={(e) => setHasSpoilers(e.target.checked)} />
        Contains spoilers
      </label>
      <Button onClick={submit} disabled={busy || body.trim().length < 10}>
        {busy ? "Posting…" : "Post review"}
      </Button>
    </div>
  );
}
