"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { MatchBadge, Pill } from "./ContentBadge";
import { SimilarContent } from "./SimilarContent";
import { ContextualRating } from "@/components/rating/ContextualRating";
import { Breadcrumb } from "@/components/layout/Breadcrumb";
import { PosterImage } from "@/components/ui/PosterImage";
import { YouTubePlayer } from "@/components/player/YouTubePlayer";
import { useToast } from "@/components/ui/Toast";
import { useEventTracker } from "@/hooks/useEventTracker";
import { useExplain } from "@/hooks/useUniqueFeatures";

export function RichContentDetail({ id }: { id: string }) {
  const { track } = useEventTracker();
  const toast = useToast();
  const [spoilerFree, setSpoilerFree] = useState(false);
  const [trailerOpen, setTrailerOpen] = useState(false);

  const { data, isLoading, isError } = useQuery<any>({
    queryKey: ["content", id],
    queryFn: async () => (await api.get(`/content/${id}`)).data,
  });
  const { data: badges } = useQuery<any>({
    queryKey: ["badges", id],
    queryFn: async () => (await api.get(`/content/${id}/badges`)).data,
    enabled: !!id,
  });
  const { data: streaming } = useQuery<any>({
    queryKey: ["streaming", id],
    queryFn: async () => (await api.get(`/content/${id}/streaming`)).data,
    enabled: !!id,
  });
  const { data: reviews } = useQuery<any>({
    queryKey: ["reviews", id],
    queryFn: async () => (await api.get(`/content/${id}/reviews`)).data,
    enabled: !!id,
  });
  const { data: spoiler } = useQuery<any>({
    queryKey: ["spoiler", id],
    queryFn: async () => (await api.get(`/content/${id}/spoiler-free`)).data,
    enabled: !!id && spoilerFree,
  });
  const explain = useExplain(id);

  if (isLoading) return <div className="p-8 text-white/70">Loading…</div>;
  if (isError || !data) return <div className="p-8 text-red-400">Content not found.</div>;

  const ytId = data.youtube_trailer_id || (data.trailer_url?.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/)?.[1] ?? null);
  const backdrop = data.backdrop_url || data.thumbnail_url;

  return (
    <div>
      {/* Hero backdrop */}
      <div className="relative h-[55vh] min-h-[360px] w-full overflow-hidden">
        <PosterImage src={backdrop} alt={data.title} className="h-full w-full" rounded="" variant="backdrop" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-black/30 to-black" />
        <div className="absolute inset-y-0 left-0 w-full md:w-3/5 bg-gradient-to-r from-black/90 via-black/60 to-transparent" />
        <div className="absolute left-0 bottom-0 p-6 md:p-10 max-w-3xl">
          <h1 className="text-3xl md:text-5xl font-extrabold drop-shadow-lg">{data.title}</h1>
          <div className="mt-3 flex flex-wrap gap-2 items-center">
            <Pill>{data.type}</Pill>
            {data.release_year && <Pill>{data.release_year}</Pill>}
            {data.maturity_rating && <Pill>{data.maturity_rating}</Pill>}
            {data.duration_seconds && <Pill>{Math.round(data.duration_seconds / 60)} min</Pill>}
            <MatchBadge score={Math.min(1, data.popularity_score)} />
            {badges?.badges?.map((b: any) => (
              <span key={b.kind} className="rounded bg-amber-500/20 text-amber-300 px-2 py-0.5 text-xs font-semibold">
                🏆 {b.label}
              </span>
            ))}
          </div>
          <div className="mt-5 flex flex-wrap gap-3 items-center">
            {(ytId || data.trailer_url) && (
              <Button onClick={() => setTrailerOpen(true)}>▶ Trailer</Button>
            )}
            <Link href={`/watch/${data.id}`} onClick={() => track("play", data.id)}>
              <Button variant="secondary">Play</Button>
            </Link>
            <Button variant="secondary"
              onClick={() => { track("add_to_list", data.id); toast.show("Added to My List", "success"); }}>
              + My List
            </Button>
            <Button variant="ghost" onClick={() => setSpoilerFree((x) => !x)}>
              {spoilerFree ? "Show original" : "Spoiler-free"}
            </Button>
          </div>
          {streaming?.items?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-xs text-white/60">Watch on:</span>
              {streaming.items.map((s: any) => (
                <a key={s.service} href={s.deep_link || "#"}
                  onClick={() => api.post(`/content/${data.id}/click-affiliate/${s.service}`).catch(() => {})}
                  className="rounded bg-white/10 hover:bg-white/20 px-2 py-0.5 text-xs">{s.service}</a>
              ))}
            </div>
          )}
        </div>
      </div>

      <Breadcrumb trail={[{ label: "Browse", href: "/browse" }, { label: data.title }]} />

      <div className="mx-auto max-w-5xl px-6 pb-16">
        <div className="grid md:grid-cols-[220px_1fr] gap-8 mt-6">
          <PosterImage src={data.thumbnail_url} alt={data.title} className="aspect-[2/3] w-full" />
          <div>
            <p className="text-base text-white/85 leading-relaxed">
              {spoilerFree ? (spoiler?.spoiler_free || data.description) : data.description}
            </p>
            {spoilerFree && spoiler?.ai_used && (
              <p className="mt-1 text-[10px] uppercase tracking-wider text-brand">AI-rewritten, spoiler-free</p>
            )}

            {explain.data?.ai_summary && (
              <div className="mt-5 rounded-md bg-brand/10 border border-brand/30 p-3 text-sm">
                <span className="text-xs uppercase text-brand mr-2">Why you&apos;ll like it</span>
                {explain.data.ai_summary}
              </div>
            )}

            {data.cast_names?.length > 0 && (
              <div className="mt-6">
                <div className="text-xs uppercase tracking-wider text-white/40 mb-2">Cast</div>
                <div className="flex flex-wrap gap-2">
                  {data.cast_names.slice(0, 8).map((n: string) => (
                    <span key={n} className="inline-flex items-center gap-2 rounded-full bg-white/5 pl-1 pr-3 py-1 text-xs">
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white/10 text-[10px] font-bold">
                        {n.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()}
                      </span>
                      {n}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-8 max-w-xl">
              <h3 className="text-base font-semibold mb-2">Your rating</h3>
              <ContextualRating contentId={data.id}
                onDone={() => toast.show("Rating saved — recommendations will adapt", "success")} />
            </div>

            <div className="mt-10">
              <h3 className="text-base font-semibold mb-3">Reviews ({reviews?.items?.length ?? 0})</h3>
              <div className="space-y-3">
                {reviews?.items?.length ? reviews.items.slice(0, 5).map((r: any) => (
                  <div key={r.id} className="rounded-md bg-surface-elevated p-3 ring-1 ring-white/10">
                    <div className="text-xs text-white/50 flex justify-between">
                      <span>{r.display_name}</span>
                      <span>{r.upvotes} 👍</span>
                    </div>
                    {r.has_spoilers && <span className="inline-block mt-1 text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded">contains spoilers</span>}
                    <p className="mt-2 text-sm whitespace-pre-wrap">{r.body}</p>
                  </div>
                )) : <p className="text-white/50 text-sm">No reviews yet.</p>}
              </div>
            </div>
          </div>
        </div>

        <SimilarContent contentId={data.id} />
      </div>

      {trailerOpen && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4" onClick={() => setTrailerOpen(false)}>
          <div className="w-full max-w-4xl" onClick={(e) => e.stopPropagation()}>
            <YouTubePlayer youtubeId={ytId} src={data.trailer_url} poster={backdrop} autoplay />
            <button onClick={() => setTrailerOpen(false)} className="absolute top-4 right-4 text-3xl">×</button>
          </div>
        </div>
      )}
    </div>
  );
}
