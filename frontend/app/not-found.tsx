import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-6">
      <div className="text-7xl">🍿</div>
      <h1 className="mt-4 text-3xl font-extrabold">We couldn&apos;t find that page</h1>
      <p className="mt-2 text-white/60 text-sm">The link may be broken, or the title has been removed from our catalog.</p>
      <div className="mt-6 flex gap-3">
        <Link href="/browse" className="rounded-md bg-brand px-4 py-2 text-sm font-semibold">Go home</Link>
        <Link href="/search" className="rounded-md bg-white/10 px-4 py-2 text-sm">Search</Link>
      </div>
    </div>
  );
}
