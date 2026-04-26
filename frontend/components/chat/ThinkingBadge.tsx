"use client";

import { useEffect, useState } from "react";

const STATES = [
  { icon: "🧬", label: "Reading your DNA…" },
  { icon: "📚", label: "Scanning the catalog…" },
  { icon: "🎯", label: "Ranking picks…" },
  { icon: "✍️", label: "Drafting a reply…" },
];

export function ThinkingBadge() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % STATES.length), 900);
    return () => clearInterval(t);
  }, []);
  const s = STATES[i];
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-white/[0.06] ring-1 ring-white/10 px-3 py-1.5 text-xs text-white/80 animate-[ro-fade-up_220ms_ease-out]">
      <span className="text-sm">{s.icon}</span>
      <span>{s.label}</span>
      <span className="flex gap-0.5 ml-1">
        <span className="w-1 h-1 rounded-full bg-brand animate-bounce" />
        <span className="w-1 h-1 rounded-full bg-brand animate-bounce" style={{ animationDelay: "0.12s" }} />
        <span className="w-1 h-1 rounded-full bg-brand animate-bounce" style={{ animationDelay: "0.24s" }} />
      </span>
    </div>
  );
}
