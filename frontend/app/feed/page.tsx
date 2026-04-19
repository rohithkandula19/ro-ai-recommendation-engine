"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";

export default function FeedPage() {
  const { data } = useQuery({
    queryKey: ["feed"],
    queryFn: async () => (await api.get("/users/me/feed")).data,
  });
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Friends feed</h1>
      <p className="text-sm text-white/60 mt-1">What your friends are watching, rating, reviewing.</p>
      <ul className="mt-6 space-y-3">
        {data?.items?.length ? data.items.map((r: any, i: number) => (
          <li key={i} className="rounded-md bg-surface-elevated ring-1 ring-white/10 p-4 flex gap-4">
            {r.thumbnail_url && <PosterImage src={r.thumbnail_url} alt={r.title} className="w-16 aspect-[2/3] rounded" />}
            <div className="flex-1">
              <div className="text-sm">
                <span className="font-semibold text-brand">{r.display_name}</span>
                <span className="text-white/60"> {r.kind.replace("_", " ")} </span>
                {r.content_id && r.title ? (
                  <Link href={`/browse/${r.content_id}`} className="font-semibold hover:underline">{r.title}</Link>
                ) : null}
              </div>
              <div className="text-xs text-white/40 mt-1">{new Date(r.created_at).toLocaleString()}</div>
            </div>
          </li>
        )) : <p className="text-white/60 text-sm">Nothing here yet — add friends to see their activity.</p>}
      </ul>
    </div>
  );
}
