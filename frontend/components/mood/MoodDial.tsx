"use client";

import { useRef, useState } from "react";

interface Props {
  value: { chill_tense: number; light_thoughtful: number };
  onChange: (v: { chill_tense: number; light_thoughtful: number }) => void;
  size?: number;
}

export function MoodDial({ value, onChange, size = 220 }: Props) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [dragging, setDragging] = useState(false);

  function setFromPointer(e: React.PointerEvent | PointerEvent) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
    onChange({ chill_tense: x, light_thoughtful: y });
  }

  return (
    <div
      ref={ref}
      className="relative mx-auto cursor-crosshair rounded-xl bg-surface-elevated ring-1 ring-white/10 select-none touch-none"
      style={{ width: size, height: size }}
      onPointerDown={(e) => {
        (e.target as Element).setPointerCapture(e.pointerId);
        setDragging(true);
        setFromPointer(e);
      }}
      onPointerMove={(e) => { if (dragging) setFromPointer(e); }}
      onPointerUp={() => setDragging(false)}
    >
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-blue-500/20 via-transparent to-red-500/30 rounded-xl" />
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-tr from-green-400/15 to-purple-500/20 rounded-xl" />

      <span className="absolute top-2 left-3 text-[10px] text-white/60">chill</span>
      <span className="absolute top-2 right-3 text-[10px] text-white/60">tense</span>
      <span className="absolute bottom-2 left-3 text-[10px] text-white/60">light</span>
      <span className="absolute bottom-2 right-3 text-[10px] text-white/60">dark</span>

      <div
        className="absolute w-6 h-6 rounded-full border-2 border-white bg-brand shadow-lg -translate-x-1/2 -translate-y-1/2 pointer-events-none"
        style={{
          left: `${value.chill_tense * 100}%`,
          top: `${value.light_thoughtful * 100}%`,
        }}
      />

      <div className="absolute bottom-1 right-2 text-[10px] text-white/40">
        {Math.round(value.chill_tense * 100)}·{Math.round(value.light_thoughtful * 100)}
      </div>
    </div>
  );
}
