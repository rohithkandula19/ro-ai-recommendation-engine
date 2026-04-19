"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Collection { slug: string; title: string }

export default function CollectionsPage() {
  const { data } = useQuery<{ items: Collection[] }>({
    queryKey: ["collections"],
    queryFn: async () => (await api.get("/collections")).data,
  });
  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Collections</h1>
      <p className="text-sm text-white/60 mt-1">Curated sets built from vibe + mood signals — not just genre.</p>
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.items.map((c) => (
          <Link key={c.slug} href={`/collections/${c.slug}`}
            className="group rounded-lg bg-surface-elevated ring-1 ring-white/10 p-6 hover:bg-white/5 transition">
            <div className="text-xl font-bold group-hover:text-brand">{c.title}</div>
            <div className="mt-2 text-xs text-white/50">Explore →</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
