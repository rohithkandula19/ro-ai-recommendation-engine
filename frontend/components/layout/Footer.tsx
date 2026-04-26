import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-16 px-14 py-10 text-xs text-[#737373]">
      <div className="mx-auto max-w-5xl space-y-4">
        <nav className="flex flex-wrap gap-x-5 gap-y-2">
          <Link href="/legal/privacy" className="hover:text-[#b3b3b3] transition-colors">Privacy</Link>
          <Link href="/legal/terms" className="hover:text-[#b3b3b3] transition-colors">Terms of Use</Link>
          <Link href="/legal/cookies" className="hover:text-[#b3b3b3] transition-colors">Cookie Preferences</Link>
          <Link href="/legal/attributions" className="hover:text-[#b3b3b3] transition-colors">Attributions</Link>
          <Link href="/docs" className="hover:text-[#b3b3b3] transition-colors">API Docs</Link>
          <Link href="/chat" className="hover:text-[#b3b3b3] transition-colors">Ask RO</Link>
        </nav>
        <p>© {new Date().getFullYear()} RO RecEngine · Data from TMDB, Trakt, TVMaze, OMDb</p>
      </div>
    </footer>
  );
}
