"use client";

import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { useRecommendations } from "@/hooks/useRecommendations";
import { useEventTracker } from "@/hooks/useEventTracker";

export function HeroSection() {
  const { data } = useRecommendations("home", 1);
  const { track } = useEventTracker();
  const featured = data?.items?.[0];

  return (
    <div className="relative h-[65vh] min-h-[420px] w-full overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-black/40 to-black" />
      {featured?.thumbnail_url && (
        <img
          src={featured.thumbnail_url}
          alt={featured.title}
          className="h-full w-full object-cover"
        />
      )}
      <div className="absolute left-0 bottom-0 p-8 md:p-14 max-w-2xl">
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight">
          {featured?.title ?? "Welcome"}
        </h1>
        <p className="mt-3 text-white/80 text-sm md:text-base">
          {featured?.reason_text ?? "Personalised picks powered by our AI recommendation engine."}
        </p>
        <div className="mt-6 flex gap-3">
          {featured && (
            <Link href={`/watch/${featured.id}`} onClick={() => track("play", featured.id)}>
              <Button variant="primary">▶ Play</Button>
            </Link>
          )}
          {featured && (
            <Link href={`/browse/${featured.id}`}>
              <Button variant="secondary">ℹ More info</Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
