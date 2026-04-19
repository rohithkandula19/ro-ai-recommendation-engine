"use client";

import { useTasteDNA, VibeVector } from "@/hooks/useUniqueFeatures";

const AXES: { key: keyof VibeVector; label: string }[] = [
  { key: "pace", label: "Pace" },
  { key: "emotion", label: "Emotion" },
  { key: "darkness", label: "Darkness" },
  { key: "humor", label: "Humor" },
  { key: "complexity", label: "Complexity" },
  { key: "spectacle", label: "Spectacle" },
];

export function TasteRadar({ size = 300 }: { size?: number }) {
  const { data, isLoading } = useTasteDNA();
  if (isLoading) return <div className="h-[300px] w-[300px] animate-pulse rounded-full bg-surface-elevated" />;
  if (!data) return null;

  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 40;
  const n = AXES.length;

  const point = (r: number, i: number) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  };

  const gridLevels = [0.25, 0.5, 0.75, 1];
  const dnaPoints = AXES.map((a, i) => point(radius * data.dna[a.key], i));

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {gridLevels.map((lvl) => (
          <polygon
            key={lvl}
            points={AXES.map((_, i) => point(radius * lvl, i).join(",")).join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={1}
          />
        ))}
        {AXES.map((_, i) => {
          const [x, y] = point(radius, i);
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.06)" />;
        })}
        <polygon
          points={dnaPoints.map((p) => p.join(",")).join(" ")}
          fill="rgba(229,9,20,0.28)"
          stroke="#E50914"
          strokeWidth={2}
        />
        {AXES.map((a, i) => {
          const [x, y] = point(radius + 22, i);
          const value = Math.round(data.dna[a.key] * 100);
          return (
            <g key={a.key}>
              <text x={x} y={y} textAnchor="middle" dominantBaseline="middle"
                    fill="rgba(255,255,255,0.85)" fontSize={12} fontWeight={600}>
                {a.label}
              </text>
              <text x={x} y={y + 14} textAnchor="middle" fill="rgba(255,255,255,0.55)" fontSize={10}>
                {value}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="mt-2 text-xs text-white/50">Taste DNA · learned from {data.samples} events</p>
    </div>
  );
}
