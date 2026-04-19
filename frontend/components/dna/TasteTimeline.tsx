"use client";

import { useDNATimeline } from "@/hooks/useQueues";

const DIMS = ["pace", "emotion", "darkness", "humor", "complexity", "spectacle"] as const;
const COLORS: Record<string, string> = {
  pace: "#60a5fa", emotion: "#f472b6", darkness: "#a78bfa",
  humor: "#fbbf24", complexity: "#34d399", spectacle: "#f87171",
};

export function TasteTimeline({ days = 90 }: { days?: number }) {
  const { data, isLoading } = useDNATimeline(days);
  if (isLoading) return <div className="h-40 animate-pulse bg-surface-elevated rounded-md" />;

  const points: any[] = data?.points ?? [];
  if (points.length < 2) {
    return (
      <div className="rounded-md bg-surface-elevated p-4 text-sm text-white/60">
        Not enough history yet. After a few days of watching, your DNA evolution will show up here.
      </div>
    );
  }

  const W = 720, H = 180, PAD = 24;
  const xStep = points.length > 1 ? (W - 2 * PAD) / (points.length - 1) : 0;

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        {[0.25, 0.5, 0.75].map((y) => (
          <line key={y} x1={PAD} x2={W - PAD} y1={PAD + (H - 2 * PAD) * (1 - y)} y2={PAD + (H - 2 * PAD) * (1 - y)} stroke="rgba(255,255,255,0.06)" />
        ))}
        {DIMS.map((d) => {
          const path = points.map((p, i) => {
            const x = PAD + i * xStep;
            const y = PAD + (H - 2 * PAD) * (1 - (p[d] ?? 0.5));
            return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
          }).join(" ");
          return <path key={d} d={path} stroke={COLORS[d]} strokeWidth={1.5} fill="none" />;
        })}
      </svg>
      <div className="flex flex-wrap gap-3 mt-2 text-xs">
        {DIMS.map((d) => (
          <span key={d} className="flex items-center gap-1">
            <span className="w-3 h-0.5 rounded" style={{ background: COLORS[d] }} />
            <span className="text-white/70 capitalize">{d}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
