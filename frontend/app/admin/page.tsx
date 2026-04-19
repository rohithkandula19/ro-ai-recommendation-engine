"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

interface Overview {
  generated_at: string;
  users: { total: number; active_7d: number };
  content: { total: number };
  events: { total: number; last_7d: number };
  feedback: { total: number; positive: number; negative: number; positive_rate: number };
  catalog: { avg_completion_rate: number };
}

interface TopContent { id: string; title: string; type: string; release_year: number; plays: number; likes: number; popularity_score: number }
interface TopGenre { genre: string; events: number }
interface Series { day: string; [event: string]: any }

function Stat({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg bg-surface-elevated px-5 py-4 ring-1 ring-white/10">
      <div className="text-xs uppercase tracking-wider text-white/50">{label}</div>
      <div className="mt-1 text-2xl font-bold">{value}</div>
      {sub && <div className="text-xs text-white/50 mt-1">{sub}</div>}
    </div>
  );
}

function BarList({ items, valueKey, labelKey, max }: { items: any[]; valueKey: string; labelKey: string; max?: number }) {
  const peak = max ?? Math.max(1, ...items.map((i) => i[valueKey]));
  return (
    <ul className="space-y-2 text-sm">
      {items.map((it, idx) => (
        <li key={idx}>
          <div className="flex justify-between">
            <span className="truncate">{it[labelKey]}</span>
            <span className="text-white/60">{it[valueKey]}</span>
          </div>
          <div className="mt-1 h-1.5 rounded bg-white/10 overflow-hidden">
            <div className="h-full bg-brand" style={{ width: `${(it[valueKey] / peak) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function AdminPage() {
  const user = useAuthStore((s) => s.user);
  const router = useRouter();

  useEffect(() => {
    if (user !== null && !user.is_admin) router.replace("/browse");
  }, [user, router]);

  const overview = useQuery<Overview>({ queryKey: ["adm-overview"], queryFn: async () => (await api.get("/admin/analytics/overview")).data });
  const topContent = useQuery<{ items: TopContent[] }>({ queryKey: ["adm-top"], queryFn: async () => (await api.get("/admin/analytics/top-content")).data });
  const topGenres = useQuery<{ items: TopGenre[] }>({ queryKey: ["adm-genres"], queryFn: async () => (await api.get("/admin/analytics/top-genres")).data });
  const series = useQuery<{ series: Series[] }>({ queryKey: ["adm-series"], queryFn: async () => (await api.get("/admin/analytics/events-timeseries?days=14")).data });

  if (overview.isLoading) return <div className="p-8 text-white/60">Loading admin dashboard…</div>;
  if (overview.isError) return <div className="p-8 text-red-400">Admin API error — are you logged in as an admin?</div>;

  const o = overview.data!;
  return (
    <div className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      <section>
        <h1 className="text-2xl font-bold">Admin analytics</h1>
        <p className="text-xs text-white/50">Generated {new Date(o.generated_at).toLocaleString()}</p>
      </section>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Users" value={o.users.total} sub={`${o.users.active_7d} active · 7d`} />
        <Stat label="Content" value={o.content.total} sub={`avg completion ${Math.round(o.catalog.avg_completion_rate * 100)}%`} />
        <Stat label="Events" value={o.events.total.toLocaleString()} sub={`${o.events.last_7d.toLocaleString()} · 7d`} />
        <Stat label="Positive feedback" value={`${Math.round(o.feedback.positive_rate * 100)}%`} sub={`${o.feedback.total} total`} />
      </section>

      <section className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-lg font-semibold mb-3">Top content</h2>
          {topContent.data && (
            <BarList
              items={topContent.data.items.map((c) => ({ ...c, label: `${c.title} (${c.release_year})` }))}
              valueKey="plays" labelKey="label"
            />
          )}
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-3">Top genres</h2>
          {topGenres.data && <BarList items={topGenres.data.items} valueKey="events" labelKey="genre" />}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Events (last 14 days)</h2>
        {series.data?.series.length ? (
          <div className="flex items-end gap-1 h-32">
            {series.data.series.map((d, idx) => {
              const total = Object.entries(d).filter(([k]) => k !== "day").reduce((a, [, v]) => a + (v as number), 0);
              const peak = Math.max(1, ...series.data!.series.map((x) =>
                Object.entries(x).filter(([k]) => k !== "day").reduce((a, [, v]) => a + (v as number), 0)));
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full bg-brand rounded-sm" style={{ height: `${(total / peak) * 100}%` }} title={`${d.day}: ${total}`} />
                  <span className="text-[9px] text-white/40">{d.day.slice(5, 10)}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-white/60 text-sm">No event data yet.</p>
        )}
      </section>
    </div>
  );
}
