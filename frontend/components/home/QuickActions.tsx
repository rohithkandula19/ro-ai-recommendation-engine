"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

export function QuickRate({ contentId }: { contentId: string }) {
  const [hover, setHover] = useState(0);
  const [saved, setSaved] = useState(0);
  const toast = useToast();

  async function submit(n: number) {
    setSaved(n);
    try {
      await api.post(`/users/me/ratings/${contentId}`, { rating: n });
      toast.show(`Rated ${n}★`, "success");
    } catch {}
  }

  return (
    <div className="flex gap-0.5" onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button key={n} onClick={(e) => { e.stopPropagation(); e.preventDefault(); submit(n); }}
          onMouseEnter={() => setHover(n)}
          className={`text-base ${(hover || saved) >= n ? "text-yellow-400" : "text-white/20"}`}>
          ★
        </button>
      ))}
    </div>
  );
}


export function MarkWatched({ contentId }: { contentId: string }) {
  const [done, setDone] = useState(false);
  async function mark(e: React.MouseEvent) {
    e.preventDefault(); e.stopPropagation();
    setDone(true);
    try {
      await api.post("/chat/action", { intent: "mark_watched", content_id: contentId });
    } catch { setDone(false); }
  }
  return (
    <button onClick={mark} aria-label="mark watched"
      className={`rounded-full w-6 h-6 flex items-center justify-center text-xs
        ${done ? "bg-emerald-500 text-white" : "bg-white/10 hover:bg-white/20"}`}>
      ✓
    </button>
  );
}
