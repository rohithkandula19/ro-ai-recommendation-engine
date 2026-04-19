"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { api, getAccessToken } from "@/lib/api";
import { VoiceMic } from "./VoiceMic";

interface Turn { role: "user" | "assistant"; content: string; actions?: Action[] }
interface Action { kind: string; content_id: string; label: string }

const STATIC_SUGGESTIONS = [
  "what should I watch tonight?",
  "something funny under 2 hours",
  "summarize my taste",
  "decisive mode — just pick one",
];

function speak(text: string) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.slice(0, 500));
  u.rate = 1.05; u.pitch = 1;
  window.speechSynthesis.speak(u);
}

function linkifyTitles(text: string, titleMap: Record<string, string>) {
  if (!Object.keys(titleMap).length) return text;
  let out: (string | JSX.Element)[] = [text];
  Object.entries(titleMap).forEach(([title, id], idx) => {
    const re = new RegExp(`\\b${title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "g");
    const next: (string | JSX.Element)[] = [];
    for (const part of out) {
      if (typeof part !== "string") { next.push(part); continue; }
      const split = part.split(re);
      split.forEach((p, i) => {
        next.push(p);
        if (i < split.length - 1) {
          next.push(<Link key={`${idx}-${i}`} href={`/browse/${id}`} className="text-brand underline font-semibold">{title}</Link>);
        }
      });
    }
    out = next;
  });
  return out;
}

export function ChatWidget() {
  const user = useAuthStore((s) => s.user);
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [titleMap, setTitleMap] = useState<Record<string, string>>({});
  const [abort, setAbort] = useState<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Cmd+K / Ctrl+K to toggle
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault(); setOpen((o) => !o);
      } else if (e.key === "Escape" && open) {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (!user || !open || turns.length > 0) return;
    api.get<{ turns: Turn[] }>("/chat/history").then((r) => {
      if (r.data?.turns?.length) setTurns(r.data.turns);
    }).catch(() => {});
  }, [user, open, turns.length]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, streaming]);

  async function send(text: string, mode: "stream" | "agent" | "decisive" = "stream") {
    const message = text.trim();
    if (!message || streaming) return;
    setInput("");
    const pageCtx = pathname && pathname.startsWith("/browse/") ? pathname.split("/").pop() : null;
    const fullMessage = pageCtx ? `[user is viewing content ${pageCtx}] ${message}` : message;

    setTurns((t) => [...t, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setStreaming(true);
    const ac = new AbortController();
    setAbort(ac);

    try {
      const token = getAccessToken();
      const endpoint = mode === "decisive" ? "/chat/decisive" : mode === "agent" ? "/chat/agent" : "/chat/stream";
      const resp = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(mode === "decisive" ? { context: message } : { message: fullMessage }),
        signal: ac.signal,
      });

      if (mode === "stream") {
        if (!resp.ok || !resp.body) throw new Error("chat fail");
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let acc = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          acc += decoder.decode(value, { stream: true });
          setTurns((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: acc }; return n; });
        }
        if (ttsEnabled) speak(acc);
      } else if (mode === "agent") {
        const data = await resp.json();
        setTurns((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: data.reply ?? "", actions: data.actions }; return n; });
        // attach titles for mention-linking
        if (Array.isArray(data.actions)) {
          const newMap: Record<string, string> = {};
          for (const a of data.actions) newMap[a.label.replace(/^(Play|Add .*? to List|Watch|Rate|View details) ?/, "").trim()] = a.content_id;
        }
        if (ttsEnabled && data.reply) speak(data.reply);
      } else {
        const data = await resp.json();
        const reply = `▶ ${data.title}\n${data.verdict}`;
        setTurns((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: reply, actions: [{ kind: "play", content_id: data.id, label: `Play ${data.title}` }] }; return n; });
      }
    } catch (e: any) {
      if (e?.name !== "AbortError") {
        setTurns((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: "Connection hiccup. Try again." }; return n; });
      }
    } finally {
      setStreaming(false); setAbort(null);
    }
  }

  async function execAction(a: Action) {
    try {
      if (a.kind === "play") { window.location.href = `/watch/${a.content_id}`; return; }
      if (a.kind === "view_details") { window.location.href = `/browse/${a.content_id}`; return; }
      await api.post("/chat/action", { intent: a.kind, content_id: a.content_id });
    } catch {}
  }

  async function clear() { await api.post("/chat/clear"); setTurns([]); }

  async function sendFeedback(turnIdx: number, value: 1 | -1) {
    const assistant = turns[turnIdx]?.content || "";
    const userMsg = turns[turnIdx - 1]?.role === "user" ? turns[turnIdx - 1].content : null;
    try {
      await api.post("/chat/feedback", {
        turn_index: turnIdx, assistant_message: assistant, user_message: userMsg, feedback: value,
      });
    } catch {}
  }

  if (!user) return null;

  return (
    <>
      <button onClick={() => setOpen((o) => !o)} aria-label="chat (Cmd+K)"
        className="fixed bottom-6 right-6 z-40 h-14 w-14 rounded-full bg-brand shadow-lg ring-1 ring-white/10 text-2xl hover:scale-105 transition">
        {open ? "×" : "💬"}
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-40 w-[min(92vw,440px)] h-[min(80vh,620px)] rounded-xl bg-surface-elevated ring-1 ring-white/10 shadow-2xl flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand flex items-center justify-center text-sm font-black">RO</div>
              <div>
                <p className="font-semibold text-sm">Ask RO</p>
                <p className="text-[10px] text-white/50">Cmd+K to toggle · remembers forever</p>
              </div>
            </div>
            <div className="flex gap-2 items-center">
              <button onClick={() => setTtsEnabled((v) => !v)} aria-label="tts"
                className={`text-xs ${ttsEnabled ? "text-brand" : "text-white/40"}`}>🔊</button>
              <button onClick={clear} className="text-xs text-white/50 hover:text-white">Clear</button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {turns.length === 0 && (
              <div className="space-y-3">
                <p className="text-sm text-white/70">Hi {user.display_name.split(" ")[0]}.</p>
                <div className="flex flex-col gap-2">
                  {STATIC_SUGGESTIONS.map((s) => (
                    <button key={s} onClick={() => send(s, s.includes("decisive") ? "decisive" : "stream")}
                      className="text-left text-sm text-white/80 bg-white/5 hover:bg-white/10 rounded-md px-3 py-2">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {turns.map((t, i) => (
              <div key={i} className={`flex gap-2 ${t.role === "user" ? "justify-end" : "justify-start"}`}>
                {t.role === "assistant" && (
                  <div className="w-7 h-7 shrink-0 rounded-full bg-brand flex items-center justify-center text-[11px] font-black">RO</div>
                )}
                <div className={`max-w-[82%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap ${
                  t.role === "user" ? "bg-brand text-white" : "bg-white/10 text-white/90"
                }`}>
                  <div>{t.content ? linkifyTitles(t.content, titleMap) : (streaming && i === turns.length - 1 ? <span className="inline-flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-white/60 animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-white/60 animate-bounce" style={{ animationDelay: "0.15s" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-white/60 animate-bounce" style={{ animationDelay: "0.3s" }} />
                  </span> : "")}</div>
                  {t.actions && t.actions.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {t.actions.map((a, idx) => (
                        <button key={idx} onClick={() => execAction(a)}
                          className="text-xs rounded-full bg-white/10 hover:bg-brand hover:text-white px-3 py-1 transition">{a.label}</button>
                      ))}
                    </div>
                  )}
                  {t.role === "assistant" && t.content && !(streaming && i === turns.length - 1) && (
                    <div className="mt-2 flex gap-2 text-xs">
                      <button onClick={() => sendFeedback(i, 1)} className="text-white/40 hover:text-emerald-400">👍</button>
                      <button onClick={() => sendFeedback(i, -1)} className="text-white/40 hover:text-red-400">👎</button>
                      <button onClick={() => speak(t.content)} className="text-white/40 hover:text-white">🔊</button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {!streaming && turns.length > 0 && turns[turns.length - 1].role === "assistant" && (
              <div className="flex gap-1 flex-wrap pt-1">
                {["tell me more", "something similar but shorter", "what else?"].map((s) => (
                  <button key={s} onClick={() => send(s)}
                    className="text-[11px] rounded-full bg-white/5 hover:bg-white/10 px-2 py-0.5 text-white/60">{s}</button>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); send(input, input.includes("pick") || input.includes("decisive") ? "decisive" : "stream"); }}
            className="px-3 py-3 border-t border-white/10 flex gap-2 items-center">
            {streaming ? (
              <button type="button" onClick={() => abort?.abort()} className="text-xs rounded bg-red-500 px-3 py-2 font-semibold">Stop</button>
            ) : null}
            <VoiceMic onTranscript={(t) => setInput((cur) => (cur ? cur + " " : "") + t)} />
            <input value={input} onChange={(e) => setInput(e.target.value)}
              disabled={streaming} placeholder="Ask or 🎤 speak…"
              className="flex-1 rounded-md bg-black/60 px-3 py-2 text-sm ring-1 ring-white/10 focus:ring-white/30 outline-none" />
            <button type="button" onClick={() => send(input || "add the top pick to my list", "agent")}
              disabled={streaming} aria-label="agent" title="Let RO take an action"
              className="rounded-md bg-amber-500 px-2 text-sm font-semibold disabled:opacity-40">⚡</button>
            <button type="submit" disabled={streaming || !input.trim()}
              className="rounded-md bg-brand px-4 text-sm font-semibold disabled:opacity-40">
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
