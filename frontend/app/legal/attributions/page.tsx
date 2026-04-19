import Link from "next/link";

export default function AttributionsPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10 space-y-6 text-sm">
      <h1 className="text-3xl font-extrabold">Attributions</h1>
      <p className="text-white/70">RO is MIT-licensed original work. Movie/TV metadata comes from these sources:</p>

      <div className="space-y-4">
        <section className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10">
          <div className="font-semibold">TVMaze</div>
          <p className="mt-1 text-white/60">TV show data, cast, episodes, posters. Non-commercial + commercial with attribution, no key needed.</p>
          <a href="https://www.tvmaze.com/" target="_blank" rel="noreferrer" className="text-brand text-xs">tvmaze.com →</a>
        </section>
        <section className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10">
          <div className="font-semibold">Trakt</div>
          <p className="mt-1 text-white/60">Trending/popular movies & shows, real YouTube trailer links, IMDb IDs.</p>
          <a href="https://trakt.tv" target="_blank" rel="noreferrer" className="text-brand text-xs">trakt.tv →</a>
        </section>
        <section className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10">
          <div className="font-semibold">TMDB (The Movie Database)</div>
          <p className="mt-1 text-white/60">Poster and backdrop images via public CDN. This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
          <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer" className="text-brand text-xs">themoviedb.org →</a>
        </section>
        <section className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10">
          <div className="font-semibold">OMDb</div>
          <p className="mt-1 text-white/60">IMDb ratings, Rotten Tomatoes scores, awards (when enabled).</p>
          <a href="https://www.omdbapi.com/" target="_blank" rel="noreferrer" className="text-brand text-xs">omdbapi.com →</a>
        </section>
        <section className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10">
          <div className="font-semibold">YouTube</div>
          <p className="mt-1 text-white/60">Trailer embeds via iframe per YouTube Terms of Service.</p>
        </section>
      </div>

      <div className="rounded-md border border-white/20 p-4 text-xs text-white/60">
        <strong>Trademarks:</strong> Netflix® is a registered trademark of Netflix, Inc. RO is unaffiliated with and not endorsed by Netflix.
        &ldquo;Netflix-style&rdquo; is descriptive use. The RO mark is original.
      </div>

      <Link href="/legal/terms" className="text-brand text-sm">Read the full Terms →</Link>
    </div>
  );
}
