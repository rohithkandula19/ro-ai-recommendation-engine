"use client";

import Link from "next/link";

export function BrandLogo({ size = 36 }: { size?: number }) {
  return (
    <Link href="/browse" aria-label="RO home" className="inline-flex items-center gap-1 group">
      <svg width={size} height={size * 0.45} viewBox="0 0 100 45" className="transition-transform group-hover:scale-105">
        <defs>
          <linearGradient id="bl-grad" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#ff2b36" />
            <stop offset="1" stopColor="#960510" />
          </linearGradient>
        </defs>
        <path d="M 10 6 L 10 38 M 10 6 L 30 6 Q 42 6 42 17 Q 42 28 30 28 L 10 28 M 30 28 L 44 38"
          fill="none" stroke="url(#bl-grad)" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="72" cy="22" r="15" fill="none" stroke="url(#bl-grad)" strokeWidth="5" />
      </svg>
    </Link>
  );
}
