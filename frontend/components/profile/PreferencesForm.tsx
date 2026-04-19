"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import type { Genre, Preferences } from "@/types";

const MATURITY = ["G", "PG", "PG-13", "R", "NC-17", "TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"];

export function PreferencesForm() {
  const qc = useQueryClient();
  const { data: prefs } = useQuery<Preferences>({
    queryKey: ["prefs"],
    queryFn: async () => (await api.get("/users/me/preferences")).data,
  });
  const { data: genres } = useQuery<Genre[]>({
    queryKey: ["genres"],
    queryFn: async () => (await api.get("/content/genres")).data,
  });

  const [selected, setSelected] = useState<number[]>([]);
  const [language, setLanguage] = useState("en");
  const [rating, setRating] = useState("PG-13");

  useEffect(() => {
    if (prefs) {
      setSelected(prefs.genre_ids || []);
      setLanguage(prefs.preferred_language || "en");
      setRating(prefs.maturity_rating || "PG-13");
    }
  }, [prefs]);

  const save = useMutation({
    mutationFn: async () => {
      await api.put("/users/me/preferences", {
        genre_ids: selected,
        preferred_language: language,
        maturity_rating: rating,
        onboarding_complete: true,
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["prefs"] }),
  });

  function toggleGenre(id: number) {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="text-sm text-white/70">Maturity rating</label>
        <select value={rating} onChange={(e) => setRating(e.target.value)}
          className="mt-1 block w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10">
          {MATURITY.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      <div>
        <label className="text-sm text-white/70">Preferred language</label>
        <input value={language} onChange={(e) => setLanguage(e.target.value)}
          className="mt-1 block w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
      </div>

      <div>
        <label className="text-sm text-white/70">Favourite genres</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {genres?.map((g) => (
            <button key={g.id} onClick={() => toggleGenre(g.id)} type="button"
              className={`rounded-full px-3 py-1 text-sm transition ${selected.includes(g.id) ? "bg-brand text-white" : "bg-white/10 text-white/80 hover:bg-white/20"}`}>
              {g.name}
            </button>
          ))}
        </div>
      </div>

      <Button onClick={() => save.mutate()} disabled={save.isPending}>
        {save.isPending ? "Saving..." : "Save preferences"}
      </Button>
    </div>
  );
}
