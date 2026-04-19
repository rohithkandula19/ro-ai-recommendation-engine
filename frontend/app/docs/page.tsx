"use client";

import Link from "next/link";
import { useState } from "react";

interface Endpoint { method: string; path: string; summary: string; auth: boolean }

const ENDPOINTS: Record<string, Endpoint[]> = {
  "Auth": [
    { method: "POST", path: "/auth/register", summary: "Create an account", auth: false },
    { method: "POST", path: "/auth/login", summary: "Exchange credentials for JWT pair", auth: false },
    { method: "POST", path: "/auth/refresh", summary: "Rotate refresh → new access token", auth: false },
    { method: "POST", path: "/auth/2fa/setup", summary: "Begin TOTP enrollment", auth: true },
    { method: "POST", path: "/auth/sso", summary: "Sign in with Google/GitHub OAuth token", auth: false },
  ],
  "Recommendations": [
    { method: "GET", path: "/recommendations/{surface}", summary: "5 surfaces: home, trending, new_releases, etc.", auth: true },
    { method: "POST", path: "/recommendations/batch", summary: "N surfaces in one request", auth: true },
    { method: "POST", path: "/recommendations/mood", summary: "Mood-dial reranking", auth: true },
    { method: "POST", path: "/recommendations/time-budget", summary: "Fits your minutes budget", auth: true },
    { method: "GET", path: "/recommendations/anti-recs", summary: "Titles you'd hate", auth: true },
    { method: "POST", path: "/recommendations/co-viewer", summary: "Two-user blended picks", auth: true },
  ],
  "Chat / AI": [
    { method: "POST", path: "/chat/stream", summary: "Streaming LLM reply", auth: true },
    { method: "POST", path: "/chat/agent", summary: "Structured tool-call actions", auth: true },
    { method: "POST", path: "/chat/decisive", summary: "Forceful single-pick mode", auth: true },
    { method: "POST", path: "/chat/self-analysis", summary: "LLM describes your taste", auth: true },
    { method: "POST", path: "/chat/facts", summary: "Long-term memory fact", auth: true },
    { method: "GET", path: "/chat/time-machine/{year}", summary: "Top picks from any year", auth: true },
  ],
  "Features": [
    { method: "GET", path: "/wrapped/{year}", summary: "Spotify-Wrapped-style retrospective", auth: true },
    { method: "POST", path: "/blind-date/start", summary: "Hidden pick flow", auth: true },
    { method: "POST", path: "/mixer", summary: "Blend 2 users' DNAs", auth: true },
    { method: "GET", path: "/achievements", summary: "10-item skill tree", auth: true },
    { method: "GET", path: "/genre-learning/{id}", summary: "5-title ramp into a new genre", auth: true },
  ],
  "Social": [
    { method: "POST", path: "/messages", summary: "Send a DM", auth: true },
    { method: "GET", path: "/users/me/feed", summary: "Friends' activity", auth: true },
    { method: "GET", path: "/users/me/taste-twins", summary: "Most similar-taste users", auth: true },
    { method: "POST", path: "/watch-parties", summary: "Host a synced watch session", auth: true },
    { method: "POST", path: "/reviews/write", summary: "Post a review", auth: true },
  ],
  "WebSockets": [
    { method: "WS", path: "/ws/party/{room}", summary: "Real-time watch-party sync + chat", auth: true },
    { method: "WS", path: "/ws/notifications", summary: "Live notifications + presence", auth: true },
    { method: "WS", path: "/ws/chat-typing/{other}", summary: "Typing indicator for DMs", auth: true },
    { method: "WS", path: "/ws/admin/live", summary: "Live admin dashboard counters", auth: true },
  ],
};

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-emerald-500/20 text-emerald-300",
  POST: "bg-blue-500/20 text-blue-300",
  PUT: "bg-amber-500/20 text-amber-300",
  DELETE: "bg-red-500/20 text-red-300",
  WS: "bg-purple-500/20 text-purple-300",
};

export default function DocsPage() {
  const [filter, setFilter] = useState("");
  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <section>
        <p className="text-xs uppercase tracking-widest text-brand">API Reference</p>
        <h1 className="mt-2 text-5xl font-black">RO docs</h1>
        <p className="mt-3 text-white/70 max-w-2xl">
          260+ REST endpoints. 5 WebSocket channels. Full OpenAPI at{" "}
          <Link href="http://localhost:8000/docs" className="text-brand">/openapi.json</Link>.{" "}
          TypeScript SDK: <code className="text-xs">npm install @ro/client</code>.
        </p>
        <div className="mt-8">
          <input value={filter} onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter endpoints…"
            className="w-full rounded-md bg-black/60 px-4 py-3 ring-1 ring-white/10 focus:ring-white/30 outline-none" />
        </div>
      </section>

      <section className="mt-12 space-y-8">
        {Object.entries(ENDPOINTS).map(([group, eps]) => {
          const matched = eps.filter(e =>
            !filter || (e.path + e.summary).toLowerCase().includes(filter.toLowerCase())
          );
          if (matched.length === 0) return null;
          return (
            <div key={group}>
              <h2 className="text-xl font-bold mb-3 text-brand">{group}</h2>
              <div className="space-y-1">
                {matched.map((e) => (
                  <div key={`${e.method}-${e.path}`}
                    className="flex items-center gap-3 rounded-md bg-white/[0.03] hover:bg-white/[0.06] ring-1 ring-white/10 px-4 py-3 transition">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${METHOD_COLORS[e.method]}`}>
                      {e.method}
                    </span>
                    <code className="text-sm font-mono">{e.path}</code>
                    <span className="ml-auto text-xs text-white/50">{e.summary}</span>
                    {e.auth && <span title="auth required" className="text-xs">🔒</span>}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </section>

      <section className="mt-16 rounded-xl bg-brand/10 ring-1 ring-brand/30 p-8">
        <h3 className="text-2xl font-bold">Quickstart</h3>
        <pre className="mt-4 overflow-x-auto rounded bg-black/50 p-4 text-xs">{`import { RoClient } from "@ro/client";

const ro = new RoClient({ baseUrl: "https://api.ro-rec.com" });
await ro.login("user@example.com", "password");

const picks = await ro.recommendations("home");
await ro.chat.send("recommend a thriller", (tok) => process.stdout.write(tok));`}</pre>
      </section>
    </div>
  );
}
