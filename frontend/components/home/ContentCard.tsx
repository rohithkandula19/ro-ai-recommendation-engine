"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { WhyCard } from "@/components/why/WhyCard";
import { useEventTracker } from "@/hooks/useEventTracker";
import { useFeedback } from "@/hooks/useUniqueFeatures";
import type { ContentItem } from "@/types";

export function ContentCard({ item, surface = "home" }: { item: ContentItem; surface?: string }) {
  const [hovered, setHovered] = useState(false);
  const [whyOpen, setWhyOpen] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { track } = useEventTracker();
  const feedback = useFeedback();

  function onEnter() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setHovered(true), 300);
  }

  function onLeave() {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setHovered(false);
  }

  function onClick() {
    track("click", item.id);
  }

  return (
    <div
      className="group relative min-w-[220px] max-w-[260px] cursor-pointer transition-transform duration-300"
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onClick={onClick}
    >
      <Link href={`/browse/${item.id}`}>
        {item.thumbnail_url ? (
          <img
            src={item.thumbnail_url}
            alt={item.title}
            className="aspect-video w-full rounded-md object-cover"
            loading="lazy"
          />
        ) : (
          <div className="aspect-video w-full rounded-md bg-gradient-to-br from-surface-elevated to-black flex items-center justify-center">
            <span className="text-white/60 text-sm px-2 text-center">{item.title}</span>
          </div>
        )}
      </Link>

      {hovered && (
        <div className="absolute left-0 top-0 z-10 w-[320px] rounded-md bg-surface-elevated shadow-2xl ring-1 ring-white/10 -translate-y-4 -translate-x-4 scale-105 transition">
          <div className="aspect-video overflow-hidden rounded-t-md bg-black">
            {item.thumbnail_url && (
              <img src={item.thumbnail_url} alt="" className="h-full w-full object-cover opacity-90" />
            )}
          </div>
          <div className="p-3">
            <div className="flex items-center gap-2">
              <Button variant="primary" onClick={(e) => { e.stopPropagation(); track("play", item.id); window.location.href = `/watch/${item.id}`; }}>
                ▶ Play
              </Button>
              <Button variant="secondary" onClick={(e) => { e.stopPropagation(); track("add_to_list", item.id); feedback.mutate({ content_id: item.id, surface, feedback: 1 }); }}>+ List</Button>
              <Button variant="ghost" onClick={(e) => { e.stopPropagation(); track("like", item.id); feedback.mutate({ content_id: item.id, surface, feedback: 1 }); }}>👍</Button>
              <Button variant="ghost" onClick={(e) => { e.stopPropagation(); track("dislike", item.id); feedback.mutate({ content_id: item.id, surface, feedback: -1 }); }}>👎</Button>
              <Button variant="ghost" onClick={(e) => { e.stopPropagation(); setWhyOpen(true); }}>ℹ</Button>
              <span className="ml-auto text-xs text-green-400 font-semibold">
                {Math.round(item.match_score * 100)}% match
              </span>
            </div>
            <div className="mt-2 text-sm font-medium">{item.title}</div>
            <div className="mt-1 text-xs text-white/60">{item.reason_text}</div>
          </div>
        </div>
      )}
      <WhyCard contentId={whyOpen ? item.id : null} open={whyOpen} onClose={() => setWhyOpen(false)} />
    </div>
  );
}
