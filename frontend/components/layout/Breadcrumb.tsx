"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export function Breadcrumb({ trail }: { trail: { label: string; href?: string }[] }) {
  const router = useRouter();
  return (
    <nav className="px-6 pt-6 text-xs text-white/50 flex items-center gap-2">
      <button onClick={() => router.back()} className="hover:text-white">← Back</button>
      <span className="text-white/20">·</span>
      {trail.map((t, i) => (
        <span key={i} className="flex items-center gap-2">
          {t.href ? <Link href={t.href} className="hover:text-white">{t.label}</Link> : <span>{t.label}</span>}
          {i < trail.length - 1 && <span className="text-white/20">/</span>}
        </span>
      ))}
    </nav>
  );
}
