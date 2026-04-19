export function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-white/10 px-2.5 py-0.5 text-xs text-white/80">
      {children}
    </span>
  );
}

export function MatchBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return <span className="text-xs font-semibold text-green-400">{pct}% match</span>;
}
