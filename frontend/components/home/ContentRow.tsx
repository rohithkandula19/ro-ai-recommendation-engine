"use client";

import { useRecommendations } from "@/hooks/useRecommendations";
import { SkeletonRow } from "@/components/ui/SkeletonCard";
import { ContentCard } from "./ContentCard";

interface Props {
  surface: string;
  label: string;
  limit?: number;
}

export function ContentRow({ surface, label, limit = 20 }: Props) {
  const { data, isLoading, isError } = useRecommendations(surface, limit);

  if (isLoading) {
    return (
      <section className="py-2">
        <h2 className="px-6 text-lg font-semibold text-white/90">{label}</h2>
        <SkeletonRow count={6} />
      </section>
    );
  }

  if (isError) return null;
  if (!data || data.items.length === 0) {
    return (
      <section className="py-2">
        <h2 className="px-6 text-lg font-semibold text-white/90">{label}</h2>
        <div className="px-6 py-4 text-sm text-white/40">Nothing here yet — keep watching to get picks for this row.</div>
      </section>
    );
  }

  return (
    <section className="py-2">
      <h2 className="px-6 text-lg font-semibold text-white/90">{label}</h2>
      <div className="flex gap-3 overflow-x-auto px-6 py-4 scrollbar-hide row-gradient">
        {data.items.map((it) => (
          <ContentCard key={it.id} item={it} />
        ))}
      </div>
    </section>
  );
}
