"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { useAuth } from "@/hooks/useAuth";
import { MobileNav } from "./MobileNav";
import { BrandLogo } from "./BrandLogo";
import { SearchAutocomplete } from "@/components/search/SearchAutocomplete";
import { NotificationBell } from "@/components/notifications/NotificationBell";

const PRIMARY_LINKS = [
  { href: "/browse", label: "Home" },
  { href: "/movies", label: "Movies" },
  { href: "/series", label: "Series" },
  { href: "/collections", label: "Collections" },
  { href: "/explore", label: "Explore", brand: true },
];

const MORE_LINKS = [
  { href: "/ai-collections", label: "AI Builder" },
  { href: "/mixer", label: "Mixer" },
  { href: "/blind-date", label: "Blind Date" },
  { href: "/wrapped", label: "Wrapped" },
  { href: "/achievements", label: "Skill Tree" },
  { href: "/feed", label: "Feed" },
  { href: "/messages", label: "DMs" },
  { href: "/streak", label: "Streak" },
  { href: "/leaderboards", label: "Leaderboards" },
  { href: "/import", label: "Import" },
  { href: "/security", label: "Security" },
  { href: "/pro", label: "RO Plus", brand: true },
];

export function Navbar() {
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => { setMenuOpen(false); }, [pathname]);

  return (
    <header className={`sticky top-0 z-40 flex items-center justify-between gap-4 px-4 md:px-6 py-3 transition-all
      ${scrolled ? "bg-black/95 backdrop-blur-lg shadow-[0_2px_20px_rgba(0,0,0,0.4)]" : "bg-gradient-to-b from-black/90 via-black/60 to-transparent"}`}>
      <div className="flex items-center gap-4 min-w-0">
        <MobileNav />
        <BrandLogo size={32} />
        <nav className="hidden md:flex items-center gap-1 text-sm">
          {PRIMARY_LINKS.map((l) => {
            const active = pathname === l.href;
            return (
              <Link key={l.href} href={l.href}
                className={`px-3 py-1.5 rounded-md transition-colors font-medium
                  ${active ? "text-white bg-white/10" : "text-white/75 hover:text-white hover:bg-white/5"}
                  ${l.brand && !active ? "text-brand hover:text-brand" : ""}`}>
                {l.label}
              </Link>
            );
          })}
          <div className="relative">
            <button onClick={() => setMenuOpen((o) => !o)}
              aria-expanded={menuOpen}
              className={`px-3 py-1.5 rounded-md transition-colors font-medium ${
                menuOpen ? "text-white bg-white/10" : "text-white/75 hover:text-white hover:bg-white/5"
              }`}>
              More ▾
            </button>
            {menuOpen && (
              <div className="absolute top-full left-0 mt-1 w-56 rounded-lg bg-surface-elevated ring-1 ring-white/10 shadow-2xl py-1 z-50 animate-[fade-in_120ms]">
                {MORE_LINKS.map((l) => (
                  <Link key={l.href} href={l.href}
                    className={`block px-4 py-2 text-sm transition-colors
                      ${l.brand ? "text-brand font-semibold" : "text-white/80 hover:text-white hover:bg-white/5"}`}>
                    {l.label}
                  </Link>
                ))}
                {user?.is_admin && (
                  <>
                    <div className="my-1 h-px bg-white/10" />
                    <Link href="/admin" className="block px-4 py-2 text-sm text-white/80 hover:bg-white/5">Admin</Link>
                    <Link href="/admin/live" className="block px-4 py-2 text-sm text-white/80 hover:bg-white/5">Admin Live</Link>
                    <Link href="/admin/feature-flags" className="block px-4 py-2 text-sm text-white/80 hover:bg-white/5">Feature Flags</Link>
                  </>
                )}
              </div>
            )}
          </div>
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden sm:block"><SearchAutocomplete /></div>
        <NotificationBell />
        {user ? (
          <div className="group/avatar relative">
            <button className="flex items-center gap-2 rounded-full hover:bg-white/5 px-2 py-1 transition">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-bold">
                {user.display_name.split(" ").map(w => w[0]).slice(0, 2).join("")}
              </span>
              <span className="hidden lg:inline text-sm">▾</span>
            </button>
            <div className="absolute top-full right-0 mt-1 w-48 rounded-lg bg-surface-elevated ring-1 ring-white/10 shadow-2xl py-1 opacity-0 pointer-events-none group-hover/avatar:opacity-100 group-hover/avatar:pointer-events-auto transition-opacity">
              <div className="px-4 py-2 text-xs text-white/60 border-b border-white/10">{user.email}</div>
              <Link href="/profile" className="block px-4 py-2 text-sm hover:bg-white/5">Profile</Link>
              <Link href="/profiles" className="block px-4 py-2 text-sm hover:bg-white/5">Switch profile</Link>
              <Link href="/security" className="block px-4 py-2 text-sm hover:bg-white/5">Security</Link>
              <button onClick={logout} className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-white/5">Sign out</button>
            </div>
          </div>
        ) : (
          <Link href="/login" className="btn btn-brand btn-sm">Sign in</Link>
        )}
      </div>
    </header>
  );
}
