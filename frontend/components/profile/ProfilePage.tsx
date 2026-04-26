"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PreferencesForm } from "./PreferencesForm";
import { useAuthStore } from "@/store/authStore";
import { TasteRadar } from "@/components/dna/TasteRadar";
import { TasteTimeline } from "@/components/dna/TasteTimeline";
import { QueuesPanel } from "@/components/queues/QueuesPanel";
import { Button } from "@/components/ui/Button";
import { useTasteDNA } from "@/hooks/useUniqueFeatures";
import { SubscriptionPicker } from "@/components/content/SubscriptionPicker";

interface HistoryItem {
  content_id: string;
  watch_pct: number;
  total_seconds_watched: number;
  completed: boolean;
  last_watched_at: string;
}

function exportDNA(user: any, dna: any) {
  const payload = {
    exported_at: new Date().toISOString(),
    user: {
      id: user?.id,
      email: user?.email,
      display_name: user?.display_name,
    },
    taste_dna: dna,
    note: "Portable profile — can be imported to any recommender that accepts the RO DNA spec.",
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ro-taste-dna-${user?.id ?? "user"}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const { data: dna } = useTasteDNA();
  const { data: history } = useQuery<HistoryItem[]>({
    queryKey: ["history"],
    queryFn: async () => (await api.get("/users/me/history", { params: { limit: 20 } })).data,
  });

  return (
    <div className="mx-auto max-w-4xl px-6 py-10 space-y-10">
      <section>
        <h1 className="text-2xl font-bold">Your profile</h1>
        <p className="text-sm text-white/60">{user?.email}</p>
        {user && <p className="mt-1 text-xs text-white/40 font-mono">{user.id}</p>}
      </section>

      <section className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-lg font-semibold mb-3">Your taste DNA</h2>
          <TasteRadar size={320} />
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-3">Portable profile</h2>
          <p className="text-sm text-white/60 mb-4">
            Export your taste DNA as JSON. Take it anywhere. No platform else lets you do this.
          </p>
          <Button onClick={() => exportDNA(user, dna)} disabled={!dna}>
            Export my DNA
          </Button>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Taste evolution · last 90 days</h2>
        <TasteTimeline days={90} />
      </section>

      <section>
        <QueuesPanel />
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-1">My streaming services</h2>
        <p className="text-sm text-white/60 mb-4">
          Pick what you subscribe to. RO will filter recommendations so you only see what you can actually watch.
        </p>
        <SubscriptionPicker />
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Preferences</h2>
        <PreferencesForm />
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Watch history</h2>
        {history && history.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {history.map((h) => (
              <li key={h.content_id} className="flex items-center justify-between rounded-md bg-surface-elevated px-4 py-2">
                <span className="font-mono text-xs text-white/60">{h.content_id.slice(0, 8)}…</span>
                <span>{Math.round(h.watch_pct * 100)}% watched</span>
                <span className="text-white/50 text-xs">{new Date(h.last_watched_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-white/60 text-sm">Nothing watched yet.</p>
        )}
      </section>
    </div>
  );
}
