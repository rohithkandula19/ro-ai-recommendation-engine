"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { useAuth } from "@/hooks/useAuth";
import { MobileNav } from "./MobileNav";
import { SearchAutocomplete } from "@/components/search/SearchAutocomplete";

export function Navbar() {
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState("");

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (q) router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between gap-6 bg-gradient-to-b from-black/90 to-black/60 px-6 py-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <MobileNav />
        <Link href="/browse" className="text-2xl font-extrabold text-brand tracking-tight">RO</Link>
        <nav className="hidden md:flex items-center gap-4 text-sm">
          <Link href="/browse" className="hover:text-white/80">Home</Link>
          <Link href="/movies" className="hover:text-white/80">Movies</Link>
          <Link href="/series" className="hover:text-white/80">Series</Link>
          <Link href="/collections" className="hover:text-white/80">Collections</Link>
          <Link href="/ai-collections" className="hover:text-white/80">AI Builder</Link>
          <Link href="/explore" className="hover:text-white/80 text-brand">Explore</Link>
          <Link href="/search" className="hover:text-white/80">Search</Link>
          <Link href="/profiles" className="hover:text-white/80">Profiles</Link>
          <Link href="/notifications" className="hover:text-white/80">🔔</Link>
          <Link href="/leaderboards" className="hover:text-white/80 text-white/50">Boards</Link>
          <Link href="/security" className="hover:text-white/80 text-white/50">Security</Link>
          <Link href="/import" className="hover:text-white/80 text-white/50">Import</Link>
          {user?.is_admin && <Link href="/admin" className="hover:text-white/80 text-white/50">Admin</Link>}
        </nav>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden sm:block"><SearchAutocomplete /></div>
        {user ? (
          <>
            <span className="hidden md:inline text-sm text-white/70">{user.display_name}</span>
            <button onClick={logout} className="text-sm text-white/70 hover:text-white">Sign out</button>
          </>
        ) : (
          <Link href="/login" className="text-sm text-white/80 hover:text-white">Sign in</Link>
        )}
      </div>
    </header>
  );
}
