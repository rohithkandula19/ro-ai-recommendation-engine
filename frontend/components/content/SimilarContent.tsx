"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ContentItem } from "@/types";
import { ContentCard } from "@/components/home/ContentCard";

export function SimilarContent({ contentId, title }: { contentId: string; title?: string }) {
  const { data } = useQuery<{ items: ContentItem[] }>({
    queryKey: ["similar", contentId, title],
    queryFn: async () => {
      try {
        if (title) {
          const r = await api.post("/search/semantic", { query: title, limit: 12 });
          const items: ContentItem[] = (r.data.results ?? [])
            .filter((x: any) => x.id !== contentId)
            .map((x: any) => ({
              id: x.id,
              title: x.title,
              type: x.type,
              thumbnail_url: x.thumbnail_url,
              match_score: 0,
              reason_text: "Similar title",
              genre_ids: [],
            }));
          return { items };
        }
        const r = await api.get("/recommendations/because_you_watched", { params: { limit: 12 } });
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
