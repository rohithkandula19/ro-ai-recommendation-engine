"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  src: string;             // .m3u8 (HLS) / .mpd (DASH) / .mp4
  poster?: string;
  autoplay?: boolean;
}

/**
 * Adaptive streaming player.
 * - Safari plays HLS natively.
 * - Everywhere else, lazy-loads hls.js from a CDN.
 * - Falls back to plain <video> for .mp4.
 */
export function HlsPlayer({ src, poster, autoplay = false }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [quality, setQuality] = useState<string>("auto");
  const [levels, setLevels] = useState<{ label: string; index: number }[]>([]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const isHls = /\.m3u8(\?|$)/i.test(src);
    if (!isHls) {
      video.src = src;
      return;
    }

    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      return;
    }

    let hls: any;
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/hls.js@1.5.14/dist/hls.min.js";
    script.onload = () => {
      const Hls = (window as any).Hls;
      if (!Hls?.isSupported()) { video.src = src; return; }
      hls = new Hls({ enableWorker: true, lowLatencyMode: true, capLevelToPlayerSize: true });
      hls.loadSource(src);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, (_: any, data: any) => {
        setLevels([{ label: "Auto", index: -1 }, ...data.levels.map((l: any, i: number) => ({
          label: `${l.height}p`, index: i,
        }))]);
      });
    };
    document.head.appendChild(script);
    return () => { hls?.destroy?.(); script.remove(); };
  }, [src]);

  return (
    <div className="relative aspect-video w-full bg-black">
      <video ref={videoRef} poster={poster} controls playsInline autoPlay={autoplay}
        className="w-full h-full" />
      {levels.length > 1 && (
        <select value={quality}
          onChange={(e) => {
            const v = e.target.value; setQuality(v);
            const hls = (window as any)._hls;
            if (hls) hls.currentLevel = v === "auto" ? -1 : Number(v);
          }}
          className="absolute top-2 right-2 bg-black/70 text-white text-xs rounded px-2 py-1">
          {levels.map((l) => <option key={l.index} value={l.index}>{l.label}</option>)}
        </select>
      )}
    </div>
  );
}
