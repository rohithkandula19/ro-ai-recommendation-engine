"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Profile { id: string; name: string; avatar_emoji: string; is_kid: boolean; max_maturity: string; has_pin: boolean }

const AVATARS = ["🎬", "🎭", "🦸", "👾", "🐱", "🦊", "🐙", "🚀", "🧠", "🌈"];

export default function ProfilesPage() {
  const qc = useQueryClient();
  const { data } = useQuery<{ items: Profile[] }>({
    queryKey: ["profiles"],
    queryFn: async () => (await api.get("/profiles")).data,
  });
  const [newName, setNewName] = useState("");
  const [newAvatar, setNewAvatar] = useState("🎬");
  const [isKid, setIsKid] = useState(false);

  const create = useMutation({
    mutationFn: async () => (await api.post("/profiles", { name: newName, avatar_emoji: newAvatar, is_kid: isKid, max_maturity: isKid ? "PG" : "R" })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["profiles"] }); setNewName(""); },
  });
  const del = useMutation({
    mutationFn: async (id: string) => { await api.delete(`/profiles/${id}`); },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profiles"] }),
  });

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="text-3xl font-extrabold text-center">Who&apos;s watching?</h1>

      <div className="mt-12 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6 justify-center">
        {data?.items.map((p) => (
          <div key={p.id} className="group relative text-center">
            <div className="mx-auto text-7xl">{p.avatar_emoji}</div>
            <div className="mt-2 font-semibold">{p.name}</div>
            {p.is_kid && <div className="text-xs text-white/50">Kids · max {p.max_maturity}</div>}
            {(data?.items.length ?? 0) > 1 && (
              <button onClick={() => { if (confirm(`Delete ${p.name}?`)) del.mutate(p.id); }}
                className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 text-white/40 hover:text-red-400">×</button>
            )}
          </div>
        ))}
      </div>

      <div className="mt-16 rounded-lg bg-surface-elevated ring-1 ring-white/10 p-5 max-w-md mx-auto">
        <h2 className="text-lg font-semibold mb-3">Add a profile</h2>
        <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Name"
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <div className="mt-3 flex gap-1 flex-wrap">
          {AVATARS.map((a) => (
            <button key={a} type="button" onClick={() => setNewAvatar(a)}
              className={`text-3xl p-2 rounded-md ${newAvatar === a ? "bg-brand" : "bg-white/5 hover:bg-white/10"}`}>{a}</button>
          ))}
        </div>
        <label className="mt-3 flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isKid} onChange={(e) => setIsKid(e.target.checked)} />
          Kids profile (max maturity PG)
        </label>
        <Button onClick={() => create.mutate()} className="mt-4 w-full" disabled={!newName.trim()}>Add profile</Button>
      </div>
    </div>
  );
}
