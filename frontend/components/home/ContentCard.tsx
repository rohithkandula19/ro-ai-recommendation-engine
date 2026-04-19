"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { PosterImage } from "@/components/ui/PosterImage";
import { WhyCard } from "@/components/why/WhyCard";
import { MatchBadge } from "@/components/content/ContentBadge";
import { useEventTracker } from "@/hooks/useEventTracker";
import { useFeedback } from "@/hooks/useUniqueFeatures";
import { useToast } from "@/components/ui/Toast";
import type { ContentItem } from "@/types";

export function ContentCard({ item, surface = "home", trailerUrl }: { item: ContentItem; surface?: string; trailerUrl?: string | null }) {
  const [hovered, setHovered] = useState(false);
  const [whyOpen, setWhyOpen] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const { track } = useEventTracker();
  const feedback = useFeedback();
  const toast = useToast();

  function onEnter() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setHovered(true);
      setTimeout(() => videoRef.current?.play().catch(() => {}), 120);
    }, 400);
  }
  function onLeave() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setHovered(false);
    videoRef.current?.pause();
  }

  return (
    <div
      data-card
      tabIndex={0}
      className="group/card relative min-w-[160px] w-[160px] sm:w-[180px] md:w-[200px] card-hover rounded-md outline-none"
      onMouseEnter={onEnter} onMouseLeave={onLeave} onFocus={onEnter} onBlur={onLeave}
    >
      <Link href={`/browse/${item.id}`} onClick={() => track("click", item.id)} tabIndex={-1}>
        <PosterImage src={item.thumbnail_url} alt={item.title} className="aspect-[2/3] w-full" />
      </Link>

      {/* Title + match beneath (always visible, helps when no hover) */}
      <div className="mt-2 px-0.5">
        <div className="text-sm font-semibold text-white truncate-word">{item.title}</div>
        <div className="mt-0.5 text-[11px] text-white/60 line-clamp-1">{item.reason_text}</div>
      </div>

      {hovered && (
        <div className="absolute left-1/2 -top-2 z-20 w-[340px] -translate-x-1/2 -translate-y-full
                        rounded-lg bg-surface-elevated shadow-2xl ring-1 ring-white/10 overflow-hidden
                        animate-[ro-fade-up_180ms_ease-out]">
          <div className="aspect-video overflow-hidden bg-black">
            {trailerUrl ? (
              <video ref={videoRef} src={trailerUrl} muted loop playsInline
                className="h-full w-full object-cover" />
            ) : (
              <PosterImage src={item.thumbnail_url} alt={item.title}
                className="h-full w-full" rounded="" variant="backdrop" />
            )}
          </div>
          <div className="p-3">
            <div className="flex items-center gap-1.5 flex-wrap">
              <Button variant="primary" size="sm"
                onClick={(e) => { e.stopPropagation(); e.preventDefault(); track("play", item.id);
                  window.location.href = `/watch/${item.id}`; }}>▶ Play</Button>
              <Button variant="secondary" size="sm"
                onClick={(e) => { e.stopPropagation(); e.preventDefault(); track("add_to_list", item.id);
                  feedback.mutate({ content_id: item.id, surface, feedback: 1 });
                  toast.show("Added to My List", "success"); }}>＋</Button>
              <Button variant="ghost" size="sm"
                onClick={(e) => { e.stopPropagation(); e.preventDefault(); track("like", item.id);
                  feedback.mutate({ content_id: item.id, surface, feedback: 1 });
                  toast.show("Liked", "success"); }}>👍</Button>
              <Button variant="ghost" size="sm"
                onClick={(e) => { e.stopPropagation(); e.preventDefault(); track("dislike", item.id);
                  feedback.mutate({ content_id: item.id, surface, feedback: -1 });
                  toast.show("Got it — less like this"); }}>👎</Button>
              <Button variant="ghost" size="sm"
                onClick={(e) => { e.stopPropagation(); e.preventDefault(); setWhyOpen(true); }}>ℹ</Button>
              <span className="ml-auto"><MatchBadge score={item.match_score} /></span>
            </div>
            <div className="mt-3 text-sm font-semibold text-white truncate-word">{item.title}</div>
            <div className="mt-0.5 text-xs text-white/70 line-clamp-2">{item.reason_text}</div>
          </div>
        </div>
      )}
      <WhyCard contentId={whyOpen ? item.id : null} open={whyOpen} onClose={() => setWhyOpen(false)} />
    </div>
  );
}
