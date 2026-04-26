"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";

export default function PublicProfile({ params }: { params: { email: string } }) {
  const email = decodeURIComponent((params?.email as string) || "");
  const { data, isLoading, isError } = useQuery({
    queryKey: ["pub", email],
    queryFn: async () => (await api.get(`/u/${encodeURIComponent(email)}`)).data,
    enabled: !!email,
  });
  if (isLoading) return <div className="p-8">…</div>;
  if (isError || !data) return <div className="p-8 text-red-400">User not found.</div>;
  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">{data.display_name}</h1>
      <p className="text-white/60 text-sm">{data.email} · {data.samples} events</p>
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-3">Taste DNA</h2>
        <div className="grid grid-cols-3 gap-3">
          {Object.entries(data.dna).map(([k, v]: any) => (
            <div key={k} className="rounded bg-surface-elevated p-3">
              <div className="text-xs capitalize text-white/60">{k}</div>
              <div className="mt-1 h-1.5 bg-white/10 rounded overflow-hidden">
                <div className="h-full bg-brand" style={{ width: `${Math.round(v * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-3">Top picks</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {data.top_picks?.map((p: any) => (
            <Link href={`/browse/${p.id}`} key={p.id}>
              <PosterImage src={p.thumbnail_url} alt={p.title} className="aspect-[2/3]" />
              <div className="mt-2 text-sm font-semibold truncate">{p.title}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
