"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PosterImage } from "@/components/ui/PosterImage";
import { Breadcrumb } from "@/components/layout/Breadcrumb";

interface Item {
  id: string; title: string; type: string; release_year: number | null;
  duration_seconds: number | null; thumbnail_url: string | null;
}

export default function CollectionPage({ params }: { params: { slug: string } }) {
  const slug = params?.slug as string;
  const { data } = useQuery<{ title: string; items: Item[] }>({
    queryKey: ["collection", slug],
    queryFn: async () => (await api.get(`/collections/${slug}`)).data,
    enabled: !!slug,
  });

  return (
    <div>
      <Breadcrumb trail={[{ label: "Collections", href: "/collections" }, { label: data?.title ?? "…" }]} />
      <div className="mx-auto max-w-7xl px-6 py-6">
        <h1 className="text-3xl font-extrabold">{data?.title ?? "…"}</h1>
        <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {data?.items.map((it) => (
            <Link key={it.id} href={`/browse/${it.id}`} className="group">
              <PosterImage src={it.thumbnail_url} alt={it.title} className="aspect-[2/3] w-full group-hover:ring-2 group-hover:ring-brand transition" />
              <div className="mt-2 text-sm font-semibold truncate">{it.title}</div>
              <div className="text-xs text-white/50">{it.release_year}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
