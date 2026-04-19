"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ContentItem } from "@/types";
import { ContentCard } from "@/components/home/ContentCard";

export function SimilarContent({ contentId }: { contentId: string }) {
  const { data } = useQuery<{ items: ContentItem[] }>({
    queryKey: ["similar", contentId],
    queryFn: async () => {
      try {
        const r = await api.get(`/recommendations/because_you_watched`, { params: { limit: 12 } });
        return { items: r.data.items };
      } catch {
        return { items: [] };
      }
    },
  });

  if (!data || data.items.length === 0) return null;
  return (
    <div className="mt-10">
      <h3 className="text-lg font-semibold mb-3">More like this</h3>
      <div className="flex gap-3 overflow-x-auto py-2 scrollbar-hide">
        {data.items.map((it) => <ContentCard key={it.id} item={it} />)}
      </div>
    </div>
  );
}
