"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/store/authStore";

const LINKS = [
  { href: "/browse", label: "Home" },
  { href: "/movies", label: "Movies" },
  { href: "/series", label: "Series" },
  { href: "/collections", label: "Collections" },
  { href: "/ai-collections", label: "AI Builder" },
  { href: "/explore", label: "Explore" },
  { href: "/search", label: "Search" },
  { href: "/profiles", label: "Profiles" },
  { href: "/notifications", label: "Notifications" },
  { href: "/leaderboards", label: "Leaderboards" },
  { href: "/security", label: "Security" },
  { href: "/import", label: "Import" },
];

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const user = useAuthStore((s) => s.user);

  return (
    <>
      <button aria-label="open menu" onClick={() => setOpen(true)}
        className="md:hidden text-white/80 text-2xl">☰</button>
      {open && (
        <div className="md:hidden fixed inset-0 z-50 bg-black/90" onClick={() => setOpen(false)}>
          <aside className="fixed inset-y-0 left-0 w-72 bg-surface-elevated p-6 overflow-y-auto ring-1 ring-white/10"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
              <span className="text-brand text-2xl font-extrabold">RO</span>
              <button onClick={() => setOpen(false)} aria-label="close" className="text-2xl">×</button>
            </div>
            <nav className="flex flex-col gap-1">
              {LINKS.map((l) => (
                <Link key={l.href} href={l.href} onClick={() => setOpen(false)}
                  className="px-3 py-2 rounded-md hover:bg-white/5">{l.label}</Link>
              ))}
              {user?.is_admin && (
                <Link href="/admin" onClick={() => setOpen(false)}
                  className="px-3 py-2 rounded-md hover:bg-white/5 text-white/50">Admin</Link>
              )}
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
