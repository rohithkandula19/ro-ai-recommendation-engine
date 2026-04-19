"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { MatchBadge, Pill } from "./ContentBadge";
import { SimilarContent } from "./SimilarContent";
import { ContextualRating } from "@/components/rating/ContextualRating";
import { Breadcrumb } from "@/components/layout/Breadcrumb";
import { PosterImage } from "@/components/ui/PosterImage";
import { useToast } from "@/components/ui/Toast";
import { useEventTracker } from "@/hooks/useEventTracker";
import type { Content } from "@/types";

export function ContentDetail({ id }: { id: string }) {
  const { track } = useEventTracker();
  const toast = useToast();
  const { data, isLoading, isError } = useQuery<Content>({
    queryKey: ["content", id],
    queryFn: async () => (await api.get(`/content/${id}`)).data,
  });

  if (isLoading) return <div className="p-8 text-white/70">Loading…</div>;
  if (isError || !data) return <div className="p-8 text-red-400">Content not found.</div>;

  return (
    <div>
      <Breadcrumb trail={[{ label: "Browse", href: "/browse" }, { label: data.title }]} />
      <div className="mx-auto max-w-5xl px-6 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          <PosterImage src={data.thumbnail_url} alt={data.title}
            className="w-full md:w-1/3 aspect-[2/3]" />
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{data.title}</h1>
            <div className="mt-2 flex flex-wrap gap-2">
              <Pill>{data.type}</Pill>
              {data.release_year && <Pill>{data.release_year}</Pill>}
              {data.maturity_rating && <Pill>{data.maturity_rating}</Pill>}
              {data.duration_seconds && <Pill>{Math.round(data.duration_seconds / 60)} min</Pill>}
              <MatchBadge score={Math.min(1, data.popularity_score)} />
            </div>
            <p className="mt-4 text-white/80 text-sm leading-relaxed">{data.description}</p>
            {data.director && <p className="mt-3 text-xs text-white/50">Director: {data.director}</p>}
            {data.cast_names?.length > 0 && (
              <p className="mt-1 text-xs text-white/50">Cast: {data.cast_names.slice(0, 6).join(", ")}</p>
            )}
            <div className="mt-6 flex gap-3">
              <Link href={`/watch/${data.id}`} onClick={() => track("play", data.id)}>
                <Button>▶ Play</Button>
              </Link>
              <Button variant="secondary"
                onClick={() => { track("add_to_list", data.id); toast.show("Added to My List", "success"); }}>
                + My List
              </Button>
            </div>
          </div>
        </div>
        <div className="mt-8 max-w-xl">
          <h3 className="text-base font-semibold mb-2">Your rating</h3>
          <ContextualRating contentId={data.id} onDone={() => toast.show("Rating saved — recommendations will adapt", "success")} />
        </div>
        <SimilarContent contentId={data.id} />
      </div>
    </div>
  );
}
