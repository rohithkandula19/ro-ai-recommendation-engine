"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

interface Friend { id: string; display_name: string; email: string; dna_samples: number }

export default function MessagesPage() {
  const { data } = useQuery<{ items: Friend[] }>({
    queryKey: ["friends"],
    queryFn: async () => (await api.get("/users/me/friends")).data,
  });
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-extrabold">Messages</h1>
      <p className="text-sm text-white/60 mt-1">Chat with friends about what to watch. {data?.items.length ? `${data.items.length} friends` : "Add friends first from /leaderboards or /u/{email}."}</p>
      <ul className="mt-6 space-y-1">
        {data?.items.map((f) => (
          <li key={f.id}>
            <Link href={`/messages/${f.id}`}
              className="flex items-center gap-3 rounded-md bg-surface-elevated px-4 py-3 ring-1 ring-white/10 hover:bg-white/5">
              <div className="w-10 h-10 rounded-full bg-brand/20 flex items-center justify-center font-bold">
                {f.display_name.split(" ").map(w => w[0]).slice(0,2).join("")}
              </div>
              <div className="flex-1">
                <div className="font-semibold">{f.display_name}</div>
                <div className="text-xs text-white/50">{f.dna_samples} watch events</div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
