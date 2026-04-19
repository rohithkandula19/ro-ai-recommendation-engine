import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-20 border-t border-white/5 px-6 py-6 text-xs text-white/40">
      <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <span>© {new Date().getFullYear()} RO</span>
          <span className="mx-2 text-white/20">·</span>
          <span>Data: TVMaze, Trakt, TMDB, OMDb</span>
        </div>
        <nav className="flex flex-wrap gap-4">
          <Link href="/legal/privacy" className="hover:text-white/70">Privacy</Link>
          <Link href="/legal/terms" className="hover:text-white/70">Terms</Link>
          <Link href="/legal/cookies" className="hover:text-white/70">Cookies</Link>
          <Link href="/legal/attributions" className="hover:text-white/70">Attributions</Link>
          <Link href="/docs" className="hover:text-white/70">API Docs</Link>
        </nav>
      </div>
    </footer>
  );
}
