"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

const MOODS = ["happy", "tired", "focused", "distracted", "with friends", "alone", "hungover", "buzzed"];

export function ContextualRating({ contentId, onDone }: { contentId: string; onDone?: () => void }) {
  const [rating, setRating] = useState(0);
  const [mood, setMood] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!rating) return;
    setSaving(true);
    try {
      await api.post(`/users/me/ratings/${contentId}`, {
        rating, mood_tag: mood || null, note: note || null,
      });
      onDone?.();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10 space-y-3">
      <div>
        <p className="text-sm font-semibold mb-1">Rate it</p>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} onClick={() => setRating(n)}
              className={`text-2xl ${rating >= n ? "text-yellow-400" : "text-white/20"}`}>★</button>
          ))}
        </div>
      </div>
      <div>
        <p className="text-xs text-white/60 mb-1">Mood when watching (optional)</p>
        <div className="flex flex-wrap gap-1">
          {MOODS.map((m) => (
            <button key={m} type="button" onClick={() => setMood(m === mood ? "" : m)}
              className={`rounded-full px-2.5 py-0.5 text-xs ${mood === m ? "bg-brand text-white" : "bg-white/10 text-white/70 hover:bg-white/20"}`}>
              {m}
            </button>
          ))}
        </div>
      </div>
      <textarea value={note} onChange={(e) => setNote(e.target.value)}
        placeholder="Optional note — context that made you rate this way"
        className="w-full rounded bg-black/60 px-3 py-2 text-sm ring-1 ring-white/10" rows={2} />
      <Button onClick={submit} disabled={!rating || saving}>{saving ? "Saving..." : "Submit rating"}</Button>
    </div>
  );
}
