"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { MatchBadge, Pill } from "./ContentBadge";
import { SimilarContent } from "./SimilarContent";
import { ContextualRating } from "@/components/rating/ContextualRating";
import { ReviewForm } from "./ReviewForm";
import { PosterImage } from "@/components/ui/PosterImage";
import { useToast } from "@/components/ui/Toast";
import { useEventTracker } from "@/hooks/useEventTracker";
import { useExplain } from "@/hooks/useUniqueFeatures";

export function RichContentDetail({ id }: { id: string }) {
  const { track } = useEventTracker();
  const toast = useToast();
  const [trailerPlaying, setTrailerPlaying] = useState(false);
  const [muted, setMuted] = useState(false);

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
  const explain = useExplain(id);

  if (isLoading) return (
    <div className="h-screen flex items-center justify-center text-white/40 text-sm">Loading…</div>
  );
  if (isError || !data) return (
    <div className="h-screen flex items-center justify-center text-red-400 text-sm">Content not found.</div>
  );

  const ytId = data.youtube_trailer_id || (data.trailer_url?.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/)?.[1] ?? null);
  const backdrop = data.backdrop_url || data.thumbnail_url;
  const hasTrailer = !!ytId;

  const trailerSrc = ytId
    ? `https://www.youtube.com/embed/${ytId}?autoplay=1&mute=${muted ? 1 : 0}&modestbranding=1&rel=0&playsinline=1`
    : null;

  return (
    <div className="bg-[#141414] min-h-screen">

      {/* ── Fullscreen trailer overlay ── */}
      {trailerPlaying && trailerSrc && (
        <div className="fixed inset-0 z-50 bg-black">
          <iframe
            key={trailerSrc}
            src={trailerSrc}
            title="Trailer"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
            allowFullScreen
            className="w-full h-full"
          />
          <div className="absolute top-4 right-4 flex gap-2">
            <button onClick={() => setMuted(m => !m)}
              className="h-10 w-10 rounded-full border border-white/50 bg-black/60 backdrop-blur flex items-center justify-center text-base hover:border-white transition">
              {muted ? "🔇" : "🔊"}
            </button>
            <button onClick={() => setTrailerPlaying(false)}
              className="h-10 w-10 rounded-full border border-white/50 bg-black/60 backdrop-blur flex items-center justify-center text-xl hover:border-white transition">
              ✕
            </button>
          </div>
        </div>
      )}

      {/* ── Full-width hero ── */}
      <div className="relative w-full" style={{ aspectRatio: "16/7", minHeight: 420, maxHeight: 720 }}>

        <PosterImage src={backdrop} alt={data.title} className="absolute inset-0 w-full h-full" rounded="" variant="backdrop" />

        {/* Gradient overlays */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/60 to-transparent pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-transparent to-transparent pointer-events-none" />

        {/* Bottom-left info */}
        <div className="absolute bottom-0 left-0 p-6 md:p-12 max-w-2xl">
            <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-tight drop-shadow-lg">
              {data.title}
            </h1>

            {/* Meta row */}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
              {data.imdb_rating && (
                <span className="text-green-400 font-bold">{data.imdb_rating * 10}% Match</span>
              )}
              <MatchBadge score={Math.min(1, data.popularity_score)} />
              {data.release_year && <span className="text-white/70">{data.release_year}</span>}
              {data.maturity_rating && (
                <span className="border border-white/40 px-1.5 py-0.5 text-xs font-bold text-white/80">
                  {data.maturity_rating}
                </span>
              )}
              {data.duration_seconds && (
                <span className="text-white/70">{Math.round(data.duration_seconds / 60)} min</span>
              )}
              {badges?.badges?.map((b: any) => (
                <span key={b.kind} className="text-amber-400 text-xs font-semibold">🏆 {b.label}</span>
              ))}
            </div>

            {/* Action buttons */}
            <div className="mt-5 flex flex-wrap gap-3">
              {hasTrailer && (
                <button
                  onClick={() => { setTrailerPlaying(true); track("play", data.id); }}
                  className="flex items-center gap-2 rounded bg-white text-black font-bold px-6 py-2.5 text-sm hover:bg-white/85 transition">
                  ▶ Play Trailer
                </button>
              )}
              <button
                onClick={() => { track("add_to_list", data.id); toast.show("Added to My List", "success"); }}
                className="flex items-center gap-2 rounded border-2 border-white/50 bg-black/40 text-white font-bold px-5 py-2.5 text-sm hover:border-white hover:bg-black/60 transition">
                + My List
              </button>
              <button
                onClick={() => { track("like", data.id); api.post("/recommendations/feedback", { content_id: data.id, surface: "detail", feedback: 1 }).catch(() => {}); toast.show("Liked", "success"); }}
                className="h-10 w-10 rounded-full border-2 border-white/50 bg-black/40 flex items-center justify-center text-white hover:border-white transition text-base">
                👍
              </button>
              <button
                onClick={() => { track("dislike", data.id); api.post("/recommendations/feedback", { content_id: data.id, surface: "detail", feedback: -1 }).catch(() => {}); toast.show("Got it — less like this"); }}
                className="h-10 w-10 rounded-full border-2 border-white/50 bg-black/40 flex items-center justify-center text-white hover:border-white transition text-base">
                👎
              </button>
            </div>
          </div>
      </div>

      {/* ── Below hero ── */}
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="grid md:grid-cols-[1fr_320px] gap-10">

          {/* Left — description + cast */}
          <div>
            <div className="flex flex-wrap gap-2 mb-4">
              <Pill>{data.type}</Pill>
              {data.language && <Pill>{data.language.toUpperCase()}</Pill>}
            </div>

            <p className="text-white/85 text-base leading-relaxed">
              {data.description}
            </p>

            {explain.data?.ai_summary && (
              <div className="mt-5 rounded-lg bg-brand/10 border border-brand/30 p-4 text-sm text-white/90">
                <span className="text-xs uppercase tracking-wider text-brand mr-2 font-bold">Why you&apos;ll like it</span>
                {explain.data.ai_summary}
              </div>
            )}

            {/* Your rating */}
            <div className="mt-8">
              <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-3">Your Rating</h3>
              <ContextualRating contentId={data.id}
                onDone={() => toast.show("Rating saved — recommendations will adapt", "success")} />
            </div>

            {/* Reviews */}
            <div className="mt-10">
              <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-4">
                Reviews ({reviews?.items?.length ?? 0})
              </h3>
              <div className="space-y-3">
                {reviews?.items?.length ? reviews.items.slice(0, 5).map((r: any) => (
                  <div key={r.id} className="rounded-lg bg-white/[0.04] p-4 ring-1 ring-white/10">
                    <div className="text-xs text-white/40 flex justify-between">
                      <span>{r.display_name}</span>
                      <span>{r.upvotes} 👍</span>
                    </div>
                    {r.has_spoilers && (
                      <span className="inline-block mt-1 text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded">
                        contains spoilers
                      </span>
                    )}
                    <p className="mt-2 text-sm text-white/80 leading-relaxed">{r.body}</p>
                  </div>
                )) : <p className="text-white/40 text-sm">No reviews yet — be the first.</p>}
              </div>
              <ReviewForm contentId={data.id} />
            </div>
          </div>

          {/* Right — metadata sidebar */}
          <div className="text-sm space-y-4">
            {data.cast_names?.length > 0 && (
              <div>
                <span className="text-white/40">Cast: </span>
                <span className="text-white/80">{data.cast_names.slice(0, 5).join(", ")}</span>
              </div>
            )}
            {data.director && (
              <div>
                <span className="text-white/40">Director: </span>
                <span className="text-white/80">{data.director}</span>
              </div>
            )}
            {streaming?.items?.length > 0 && (
              <div>
                <span className="text-white/40 block mb-2">Available on:</span>
                <div className="flex flex-wrap gap-2">
                  {streaming.items.map((s: any) => (
                    <a key={s.service} href={s.deep_link || "#"}
                      onClick={() => api.post(`/content/${data.id}/click-affiliate/${s.service}`).catch(() => {})}
                      className="rounded bg-white/10 hover:bg-white/20 px-3 py-1 text-xs font-medium transition">
                      {s.service}
                    </a>
                  ))}
                </div>
              </div>
            )}
            <div>
              <span className="text-white/40">This title is: </span>
              <span className="text-white/80 capitalize">{data.type}</span>
            </div>
            {data.imdb_rating && (
              <div>
                <span className="text-white/40">IMDB: </span>
                <span className="text-white/80">{data.imdb_rating}/10</span>
              </div>
            )}
            {/* Poster thumbnail */}
            <div className="pt-2">
              <PosterImage src={data.thumbnail_url} alt={data.title} className="w-full aspect-[2/3] rounded-lg" />
            </div>
          </div>
        </div>

        {/* More like this */}
        <SimilarContent contentId={data.id} title={data.title} />
      </div>
    </div>
  );
}
