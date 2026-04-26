"use client";

import Link from "next/link";

export function BrandLogo({ size = 28 }: { size?: number }) {
  return (
    <Link href="/browse" aria-label="RO RecEngine home" className="inline-flex items-center gap-2 group flex-shrink-0">
      <svg width={size} height={size} viewBox="0 0 40 40" className="flex-shrink-0 transition-opacity group-hover:opacity-80">
        <defs>
          <linearGradient id="logo-grad" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#ff2b36" />
            <stop offset="1" stopColor="#b00009" />
          </linearGradient>
        </defs>
        <path d="M4 8 L4 32 M4 8 L18 8 Q26 8 26 16 Q26 24 18 24 L4 24 M18 24 L28 32"
          fill="none" stroke="url(#logo-grad)" strokeWidth="4.5" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx="33" cy="20" r="6" fill="none" stroke="url(#logo-grad)" strokeWidth="4.5"/>
      </svg>
      <span className="text-[#E50914] font-black text-lg tracking-tight leading-none hidden sm:block">
        RecEngine
      </span>
    </Link>
  );
}
