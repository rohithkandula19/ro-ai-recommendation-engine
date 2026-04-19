"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface AIColl { id: string; name: string; prompt: string; content_ids: string[]; is_public: boolean; created_at: string }

const EXAMPLES = [
  "90s heist movies with twists",
  "slow-burn sci-fi about identity",
  "comfort shows for a rainy afternoon",
  "animated films that make adults cry",
];

export default function AICollectionsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");

  const list = useQuery<{ items: AIColl[] }>({
    queryKey: ["ai-collections"],
    queryFn: async () => (await api.get("/ai-collections")).data,
  });

  const create = useMutation({
    mutationFn: async () => (await api.post("/ai-collections", { name, prompt, is_public: false })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ai-collections"] }); setName(""); setPrompt(""); },
  });

  return (
    <div className="mx-auto max-w-4xl px-6 py-10 space-y-8">
      <section>
        <h1 className="text-3xl font-extrabold">AI Collection Builder</h1>
        <p className="text-sm text-white/60 mt-1">Describe a theme in plain English. AI picks titles from the catalog that match.</p>
      </section>

      <section className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-5 space-y-3">
        <input value={name} onChange={(e) => setName(e.target.value)}
          placeholder="Collection name (e.g. Sunday Night Picks)"
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)}
          rows={3} placeholder="Describe the vibe — any detail helps"
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <div className="flex flex-wrap gap-1">
          {EXAMPLES.map((e) => (
            <button key={e} type="button" onClick={() => setPrompt(e)}
              className="rounded-full bg-white/5 px-3 py-1 text-xs text-white/60 hover:bg-white/10">{e}</button>
          ))}
        </div>
        <Button onClick={() => create.mutate()} disabled={!name.trim() || !prompt.trim() || create.isPending}>
          {create.isPending ? "Curating…" : "Generate collection"}
        </Button>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Your collections</h2>
        {list.data?.items.length ? (
          <ul className="space-y-3">
            {list.data.items.map((c) => (
              <li key={c.id} className="rounded-md bg-surface-elevated p-4 ring-1 ring-white/10">
                <div className="flex justify-between">
                  <div>
                    <div className="font-semibold">{c.name}</div>
                    <div className="text-xs text-white/50 mt-1">&ldquo;{c.prompt}&rdquo;</div>
                  </div>
                  <span className="text-xs text-white/40">{c.content_ids.length} titles</span>
                </div>
              </li>
            ))}
          </ul>
        ) : <p className="text-white/60 text-sm">No collections yet — generate one above.</p>}
      </section>
    </div>
  );
}
