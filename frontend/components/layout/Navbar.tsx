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
  { href: "/series", label: "TV Shows" },
  { href: "/collections", label: "New & Popular" },
  { href: "/explore", label: "Explore" },
];

const MORE_LINKS = [
  { href: "/chat", label: "Ask RO", brand: true },
  { href: "/ai-collections", label: "AI Collections" },
  { href: "/mixer", label: "Mixer" },
  { href: "/blind-date", label: "Blind Date" },
  { href: "/wrapped", label: "Wrapped" },
  { href: "/achievements", label: "Achievements" },
  { href: "/feed", label: "Activity Feed" },
  { href: "/messages", label: "Messages" },
  { href: "/leaderboards", label: "Leaderboards" },
  { href: "/pro", label: "RO Plus", brand: true },
];

export function Navbar() {
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => { setMenuOpen(false); }, [pathname]);

  return (
    <header className={`sticky top-0 z-40 flex items-center justify-between gap-6 px-4 md:px-14 h-[68px] transition-all duration-500
      ${scrolled ? "bg-[#141414]" : "bg-gradient-to-b from-black/80 via-black/40 to-transparent"}`}>

      {/* Left — logo + nav */}
      <div className="flex items-center gap-8 min-w-0">
        <MobileNav />
        <BrandLogo size={28} />
        <nav className="hidden md:flex items-center gap-5 text-sm">
          {PRIMARY_LINKS.map((l) => {
            const active = pathname === l.href;
            return (
              <Link key={l.href} href={l.href}
                className={`nav-link ${active ? "active" : ""}`}>
                {l.label}
              </Link>
            );
          })}
          <div className="relative">
            <button onClick={() => setMenuOpen((o) => !o)}
              className="nav-link flex items-center gap-1">
              More
              <svg width="10" height="6" viewBox="0 0 10 6" className={`transition-transform duration-200 ${menuOpen ? "rotate-180" : ""}`}>
                <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
              </svg>
            </button>
            {menuOpen && (
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-52 rounded bg-[#141414] border border-white/10 shadow-2xl py-2 z-50 animate-[fade-in_120ms]">
                <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#141414] border-l border-t border-white/10 rotate-45" />
                {MORE_LINKS.map((l) => (
                  <Link key={l.href} href={l.href}
                    className={`block px-4 py-2 text-sm transition-colors hover:bg-white/5
                      ${l.brand ? "text-brand font-semibold" : "text-[#e5e5e5] hover:text-white"}`}>
                    {l.label}
                  </Link>
                ))}
                {user?.is_admin && (
                  <>
                    <div className="my-1 h-px bg-white/10" />
                    <Link href="/admin" className="block px-4 py-2 text-sm text-white/70 hover:bg-white/5 hover:text-white">Admin</Link>
                    <Link href="/admin/feature-flags" className="block px-4 py-2 text-sm text-white/70 hover:bg-white/5 hover:text-white">Feature Flags</Link>
                  </>
                )}
              </div>
            )}
          </div>
        </nav>
      </div>

      {/* Right — search + bell + avatar */}
      <div className="flex items-center gap-4">
        <div className="hidden sm:block"><SearchAutocomplete /></div>
        <NotificationBell />
        {user ? (
          <div className="group/avatar relative">
            <button className="flex items-center gap-1.5">
              <span className="flex h-8 w-8 items-center justify-center rounded bg-brand text-sm font-bold leading-none">
                {user.display_name.split(" ").map((w: string) => w[0]).slice(0, 2).join("").toUpperCase()}
              </span>
              <svg width="10" height="6" viewBox="0 0 10 6" className="text-white/70 transition-transform group-hover/avatar:rotate-180 duration-200">
                <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
              </svg>
            </button>
            <div className="absolute top-full right-0 mt-3 w-52 rounded bg-[#141414] border border-white/10 shadow-2xl py-2
                            opacity-0 pointer-events-none group-hover/avatar:opacity-100 group-hover/avatar:pointer-events-auto transition-opacity duration-150">
              <div className="absolute -top-1.5 right-4 w-3 h-3 bg-[#141414] border-l border-t border-white/10 rotate-45" />
              <div className="px-4 py-2 border-b border-white/10">
                <div className="text-sm font-semibold text-white">{user.display_name}</div>
                <div className="text-xs text-white/50 mt-0.5">{user.email}</div>
              </div>
              <Link href="/profile" className="block px-4 py-2 text-sm text-[#e5e5e5] hover:text-white hover:bg-white/5">Profile</Link>
              <Link href="/profiles" className="block px-4 py-2 text-sm text-[#e5e5e5] hover:text-white hover:bg-white/5">Switch Profile</Link>
              <Link href="/security" className="block px-4 py-2 text-sm text-[#e5e5e5] hover:text-white hover:bg-white/5">Account Settings</Link>
              <div className="my-1 h-px bg-white/10" />
              <button onClick={logout} className="block w-full text-left px-4 py-2 text-sm text-[#e5e5e5] hover:text-white hover:bg-white/5">
                Sign out of RO RecEngine
              </button>
            </div>
          </div>
        ) : (
          <Link href="/login" className="btn btn-brand btn-sm">Sign In</Link>
        )}
      </div>
    </header>
  );
}
