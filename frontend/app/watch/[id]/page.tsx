"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { VideoPlayer } from "@/components/player/VideoPlayer";
import type { Content } from "@/types";

const DEFAULT_VIDEO = "https://www.w3schools.com/html/mov_bbb.mp4";

export default function WatchPage() {
  const params = useParams<{ id: string }>();
  const id = (params?.id || "") as string;
  const { data } = useQuery<Content>({
    queryKey: ["content", id],
    queryFn: async () => (await api.get(`/content/${id}`)).data,
    enabled: !!id,
  });
  if (!id) return null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-6">
      <h1 className="text-xl font-semibold mb-3">{data?.title ?? "Now playing"}</h1>
      <VideoPlayer
        contentId={id}
        src={data?.trailer_url ?? DEFAULT_VIDEO}
        poster={data?.thumbnail_url ?? undefined}
      />
    </div>
  );
}
