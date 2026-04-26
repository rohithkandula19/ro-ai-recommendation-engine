"use client";

import Link from "next/link";
import { PosterImage } from "@/components/ui/PosterImage";

interface Props {
  id: string;
  title: string;
  posterUrl?: string | null;
  year?: number | null;
  type?: string | null;
}

export function InlineTitleCard({ id, title, posterUrl, year, type }: Props) {
  return (
    <Link
      href={`/browse/${id}`}
      className="group/tile my-2 flex items-center gap-3 rounded-lg bg-white/[0.04] ring-1 ring-white/10 p-2 pr-3 hover:bg-white/[0.08] lift-hover max-w-[320px]"
    >
      <div className="h-16 w-12 shrink-0 overflow-hidden rounded">
        <PosterImage src={posterUrl ?? null} alt={title} className="h-full w-full" rounded="" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold text-white truncate-word">{title}</div>
        <div className="mt-0.5 text-[11px] text-white/50 flex items-center gap-1.5">
          {type && <span className="uppercase tracking-wider">{type}</span>}
          {year && <span>· {year}</span>}
        </div>
      </div>
      <span className="text-white/30 group-hover/tile:text-brand text-lg">›</span>
    </Link>
  );
}
