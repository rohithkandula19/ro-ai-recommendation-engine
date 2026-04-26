"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { PosterImage } from "@/components/ui/PosterImage";
import { WhyCard } from "@/components/why/WhyCard";
import { useEventTracker } from "@/hooks/useEventTracker";
import { useFeedback } from "@/hooks/useUniqueFeatures";
import { useServiceFilter } from "@/hooks/useServiceFilter";
import { useToast } from "@/components/ui/Toast";
import type { ContentItem } from "@/types";

export function ContentCard({ item, surface = "home" }: { item: ContentItem; surface?: string }) {
  const [hovered, setHovered] = useState(false);
  const [whyOpen, setWhyOpen] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { track } = useEventTracker();
  const feedback = useFeedback();
  const toast = useToast();
  const { topProviderFor } = useServiceFilter();
  const myProvider = topProviderFor(item.id);

  function onEnter() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setHovered(true), 450);
  }
  function onLeave() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setHovered(false);
  }

  return (
    <div
      data-card
      tabIndex={0}
      className={`relative flex-shrink-0 w-[180px] sm:w-[200px] md:w-[220px] lg:w-[240px] rounded-sm outline-none
                  transition-all duration-200 ${hovered ? "z-30" : "z-0"}`}
      onMouseEnter={onEnter} onMouseLeave={onLeave}
      onFocus={onEnter} onBlur={onLeave}
    >
      {/* Poster */}
      <Link href={`/browse/${item.id}`} onClick={() => track("click", item.id)} tabIndex={-1}>
        <div className={`relative overflow-hidden rounded-sm transition-all duration-200
                         ${hovered ? "rounded-b-none" : ""}`}>
          <PosterImage src={item.thumbnail_url} alt={item.title} className="aspect-[2/3] w-full" rounded="" />
          {myProvider && (
            <div className="absolute top-2 left-2 rounded-sm bg-black/75 px-1.5 py-0.5 text-[10px] font-bold text-white">
              {myProvider}
            </div>
          )}
        </div>
      </Link>

      {/* Netflix-style expanding hover card */}
      {hovered && (
        <div className="absolute top-0 left-1/2 z-30 w-[300px] rounded-md overflow-hidden shadow-[0_0_40px_10px_rgba(0,0,0,0.8)]
                        ring-1 ring-white/10 bg-[#181818]"
             style={{ animation: "card-expand 200ms cubic-bezier(0.22,1,0.36,1) both", transform: "translateX(-50%)" }}>

          {/* Backdrop image */}
          <Link href={`/browse/${item.id}`} onClick={() => track("click", item.id)}>
            <div className="relative aspect-video overflow-hidden">
              <PosterImage src={item.thumbnail_url} alt={item.title} className="w-full h-full" rounded="" variant="backdrop" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#181818]/60 to-transparent" />
            </div>
          </Link>

          {/* Info panel */}
          <div className="p-3">
            {/* Action buttons */}
            <div className="flex items-center gap-2 mb-3">
              {/* Play */}
              <button
                onClick={() => { track("watch_intent", item.id); window.location.href = `/browse/${item.id}`; }}
                className="h-9 w-9 rounded-full bg-white flex items-center justify-center hover:bg-white/85 transition flex-shrink-0">
                <svg viewBox="0 0 24 24" className="w-4 h-4 text-black fill-black ml-0.5">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </button>
              {/* Add to list */}
              <button
                onClick={(e) => { e.stopPropagation();
                  feedback.mutate({ content_id: item.id, surface, feedback: 1 });
                  toast.show("Added to My List", "success"); }}
                className="h-9 w-9 rounded-full border-2 border-white/50 flex items-center justify-center hover:border-white transition text-white text-lg flex-shrink-0">
                +
              </button>
              {/* Like */}
              <button
                onClick={(e) => { e.stopPropagation(); track("like", item.id);
                  feedback.mutate({ content_id: item.id, surface, feedback: 1 });
                  toast.show("Liked", "success"); }}
                className="h-9 w-9 rounded-full border-2 border-white/50 flex items-center justify-center hover:border-white transition text-sm flex-shrink-0">
                👍
              </button>
              {/* Dislike */}
              <button
                onClick={(e) => { e.stopPropagation(); track("dislike", item.id);
                  feedback.mutate({ content_id: item.id, surface, feedback: -1 });
                  toast.show("Got it — less like this"); }}
                className="h-9 w-9 rounded-full border-2 border-white/50 flex items-center justify-center hover:border-white transition text-sm flex-shrink-0">
                👎
              </button>
              {/* Why */}
              <button
                onClick={(e) => { e.stopPropagation(); setWhyOpen(true); }}
                className="ml-auto h-9 w-9 rounded-full border-2 border-white/50 flex items-center justify-center hover:border-white transition text-white/70 text-sm flex-shrink-0">
                ⓘ
              </button>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-2 text-xs mb-1.5">
              {item.match_score > 0.3 && (
                <span className="font-bold" style={{ color: "#46d369" }}>
                  {Math.round(item.match_score * 100)}% Match
                </span>
              )}
              <span className="border border-white/30 px-1 text-white/60 text-[10px]">{item.type === "movie" ? "FILM" : "SERIES"}</span>
              {myProvider && <span className="text-white/50">{myProvider}</span>}
            </div>
            <div className="text-sm font-semibold text-white leading-snug line-clamp-1">{item.title}</div>
            {item.reason_text && (
              <div className="text-[11px] text-white/50 mt-0.5 line-clamp-1">{item.reason_text}</div>
            )}
          </div>
        </div>
      )}

      <WhyCard contentId={whyOpen ? item.id : null} open={whyOpen} onClose={() => setWhyOpen(false)} />
    </div>
  );
}
