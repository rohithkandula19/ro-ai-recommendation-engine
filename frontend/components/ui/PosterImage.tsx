"use client";

import { useState } from "react";

interface Props {
  src: string | null | undefined;
  alt: string;
  className?: string;
  rounded?: string;
}

function initials(s: string): string {
  return s.split(/\s+/).slice(0, 3).map((w) => w[0] || "").join("").toUpperCase().slice(0, 3);
}

function hashHue(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h) % 360;
}

export function PosterImage({ src, alt, className = "", rounded = "rounded-md" }: Props) {
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
  return (
    <img
      src={src} alt={alt} loading="lazy" onError={() => setFailed(true)}
      className={`${className} ${rounded} object-cover`}
    />
  );
}
