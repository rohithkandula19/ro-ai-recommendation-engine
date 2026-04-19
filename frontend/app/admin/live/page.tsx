"use client";

import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { useWebSocket } from "@/hooks/useWebSocket";

interface Tick { type: string; total_requests: number; online_users: number }

export default function AdminLivePage() {
  const user = useAuthStore((s) => s.user);
  const [history, setHistory] = useState<number[]>([]);
  const [online, setOnline] = useState(0);
  const [total, setTotal] = useState(0);
  const lastRef = useRef(0);

  useWebSocket(user?.is_admin ? "/ws/admin/live" : null, (m: Tick) => {
    if (m.type !== "tick") return;
    const delta = m.total_requests - lastRef.current;
    lastRef.current = m.total_requests;
    setTotal(m.total_requests);
    setOnline(m.online_users);
    setHistory((h) => [...h.slice(-59), delta]);
  });

  if (!user?.is_admin) return <div className="p-10 text-red-400">Admin only.</div>;

  const peak = Math.max(1, ...history);
  return (
    <div className="mx-auto max-w-5xl px-6 py-10 space-y-8">
      <h1 className="text-3xl font-extrabold">Live dashboard</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-6">
          <div className="text-xs uppercase text-white/50">Online</div>
          <div className="text-5xl font-black mt-1">{online}</div>
        </div>
        <div className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-6">
          <div className="text-xs uppercase text-white/50">Total requests</div>
          <div className="text-5xl font-black mt-1">{total.toLocaleString()}</div>
        </div>
        <div className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-6">
          <div className="text-xs uppercase text-white/50">Rate (req/2s)</div>
          <div className="text-5xl font-black mt-1 text-brand">{history[history.length - 1] ?? 0}</div>
        </div>
      </div>
      <section>
        <h2 className="text-sm font-semibold text-white/70 mb-2">Last 2 minutes</h2>
        <div className="flex items-end gap-1 h-32">
          {history.map((d, i) => (
            <div key={i} className="flex-1 bg-brand rounded-sm" style={{ height: `${(d / peak) * 100}%` }} />
          ))}
        </div>
      </section>
    </div>
  );
}
