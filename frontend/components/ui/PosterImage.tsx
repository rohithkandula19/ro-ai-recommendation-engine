"use client";

import { useState } from "react";

interface Props {
  src: string | null | undefined;
  alt: string;
  className?: string;
  rounded?: string;
  /** Hero/backdrop uses wider crop. Default = poster. */
  variant?: "poster" | "backdrop";
}

function initials(s: string): string {
  return s.split(/\s+/).slice(0, 3).map((w) => w[0] || "").join("").toUpperCase().slice(0, 3);
}

function hashHue(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h) % 360;
}

/** Upgrade TMDB image CDN size. Paths look like:
 *     https://image.tmdb.org/t/p/w500/xyz.jpg     → swap w500
 *     https://image.tmdb.org/t/p/original/xyz.jpg → keep original
 *  TVMaze `original_untouched` images are already max-res; leave alone.
 */
function tmdbResize(url: string, size: string): string {
  return url.replace(/\/t\/p\/w\d+\//, `/t/p/${size}/`).replace(/\/t\/p\/original\//, `/t/p/${size}/`);
}

function srcSet(url: string, variant: "poster" | "backdrop"): string | undefined {
  if (!url.includes("image.tmdb.org")) return undefined;
  if (variant === "backdrop") {
    return [
      `${tmdbResize(url, "w780")} 780w`,
      `${tmdbResize(url, "w1280")} 1280w`,
      `${tmdbResize(url, "original")} 1920w`,
    ].join(", ");
  }
  return [
    `${tmdbResize(url, "w342")} 342w`,
    `${tmdbResize(url, "w500")} 500w`,
    `${tmdbResize(url, "w780")} 780w`,
    `${tmdbResize(url, "original")} 1200w`,
  ].join(", ");
}

function bestSrc(url: string, variant: "poster" | "backdrop"): string {
  if (!url.includes("image.tmdb.org")) return url;
  return variant === "backdrop" ? tmdbResize(url, "w1280") : tmdbResize(url, "w780");
}

export function PosterImage({ src, alt, className = "", rounded = "rounded-md", variant = "poster" }: Props) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    const hue = hashHue(alt);
    const bg = `linear-gradient(135deg, hsl(${hue}, 45%, 18%), hsl(${(hue + 40) % 360}, 60%, 10%))`;
    return (
      <div className={`${className} ${rounded} flex items-center justify-center p-4 text-center`} style={{ background: bg }}>
        <div>
          <div className="text-2xl font-black text-white/80">{initials(alt)}</div>
          <div className="mt-1 text-xs text-white/70 line-clamp-2">{alt}</div>
        </div>
      </div>
    );
  }

  const hi = bestSrc(src, variant);
  const set = srcSet(src, variant);
  const sizes = variant === "backdrop"
    ? "(min-width: 1280px) 1920px, (min-width: 768px) 1280px, 780px"
    : "(min-width: 1024px) 342px, (min-width: 640px) 342px, 220px";

  return (
    <img
      src={hi} srcSet={set} sizes={set ? sizes : undefined}
      alt={alt} loading="lazy" decoding="async" onError={() => setFailed(true)}
      className={`${className} ${rounded} object-cover`}
      style={{ imageRendering: "auto" }}
    />
  );
}
