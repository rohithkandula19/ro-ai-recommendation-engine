"use client";

/** YouTube iframe embed — fallback to HTML5 video if no YouTube ID provided. */
export function YouTubePlayer({ youtubeId, src, poster, autoplay = false }: {
  youtubeId: string | null;
  src?: string | null;
  poster?: string | null;
  autoplay?: boolean;
}) {
  if (youtubeId) {
    const params = new URLSearchParams({
      autoplay: autoplay ? "1" : "0",
      modestbranding: "1",
      rel: "0",
      playsinline: "1",
    });
    return (
      <div className="relative aspect-video w-full bg-black">
        <iframe
          src={`https://www.youtube.com/embed/${youtubeId}?${params.toString()}`}
          title="YouTube trailer"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
          allowFullScreen
          className="absolute inset-0 w-full h-full"
        />
      </div>
    );
  }
  if (src) {
    return (
      <video src={src} poster={poster ?? undefined}
        className="aspect-video w-full bg-black" controls playsInline autoPlay={autoplay} />
    );
  }
  return <div className="aspect-video w-full bg-surface-elevated flex items-center justify-center text-white/40">No trailer available</div>;
}
