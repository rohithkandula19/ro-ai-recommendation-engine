"use client";

import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { api, getAccessToken } from "@/lib/api";

interface Turn { role: "user" | "assistant"; content: string }

const SUGGESTIONS = [
  "what should I watch tonight?",
  "something funny under 2 hours",
  "summarize my taste",
  "a thriller that won't stress me out",
];

export function ChatWidget() {
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!user || !open || turns.length > 0) return;
    api.get<{ turns: Turn[] }>("/chat/history").then((r) => {
      if (r.data?.turns?.length) setTurns(r.data.turns);
    }).catch(() => {});
  }, [user, open, turns.length]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, streaming]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || streaming) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const token = getAccessToken();
      const resp = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message }),
      });
      if (!resp.ok || !resp.body) {
        throw new Error("chat request failed");
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        acc += chunk;
        setTurns((t) => {
          const next = t.slice();
          next[next.length - 1] = { role: "assistant", content: acc };
          return next;
        });
      }
    } catch (e) {
      setTurns((t) => {
        const next = t.slice();
        next[next.length - 1] = { role: "assistant", content: "Connection hiccup. Try again." };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }

  async function clear() {
    await api.post("/chat/clear");
    setTurns([]);
  }

  async function sendFeedback(turnIdx: number, value: 1 | -1) {
    const assistant = turns[turnIdx]?.content || "";
    const userMsg = turns[turnIdx - 1]?.role === "user" ? turns[turnIdx - 1].content : null;
    try {
      await api.post("/chat/feedback", {
        turn_index: turnIdx,
        assistant_message: assistant,
        user_message: userMsg,
        feedback: value,
      });
    } catch {}
  }

  if (!user) return null;

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="chat"
        className="fixed bottom-6 right-6 z-40 h-14 w-14 rounded-full bg-brand shadow-lg ring-1 ring-white/10 text-2xl hover:scale-105 transition"
      >
        {open ? "×" : "💬"}
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-40 w-[min(92vw,420px)] h-[min(78vh,580px)] rounded-xl bg-surface-elevated ring-1 ring-white/10 shadow-2xl flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <div>
              <p className="font-semibold">Ask RO</p>
              <p className="text-[10px] text-white/50">Your personal AI recommender · remembers this conversation</p>
            </div>
            <button onClick={clear} className="text-xs text-white/50 hover:text-white">Clear</button>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {turns.length === 0 && (
              <div className="space-y-3">
                <p className="text-sm text-white/70">Hi {user.display_name.split(" ")[0]}. Ask me anything about what to watch.</p>
                <div className="flex flex-col gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} onClick={() => send(s)}
                      className="text-left text-sm text-white/80 bg-white/5 hover:bg-white/10 rounded-md px-3 py-2">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {turns.map((t, i) => (
              <div key={i} className={`flex ${t.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap ${
                  t.role === "user" ? "bg-brand text-white" : "bg-white/10 text-white/90"
                }`}>
                  {t.content || (streaming && i === turns.length - 1 ? "…" : "")}
                  {t.role === "assistant" && t.content && !(streaming && i === turns.length - 1) && (
                    <div className="mt-2 flex gap-2 text-xs">
                      <button onClick={() => sendFeedback(i, 1)} className="text-white/40 hover:text-emerald-400">👍</button>
                      <button onClick={() => sendFeedback(i, -1)} className="text-white/40 hover:text-red-400">👎</button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={(e) => { e.preventDefault(); send(input); }}
            className="px-3 py-3 border-t border-white/10 flex gap-2">
            <input value={input} onChange={(e) => setInput(e.target.value)}
              disabled={streaming} placeholder="Ask about what to watch..."
              className="flex-1 rounded-md bg-black/60 px-3 py-2 text-sm ring-1 ring-white/10 focus:ring-white/30 outline-none" />
            <button type="submit" disabled={streaming || !input.trim()}
              className="rounded-md bg-brand px-4 text-sm font-semibold disabled:opacity-40">
              {streaming ? "…" : "Send"}
            </button>
          </form>
        </div>
      )}
    </>
  );
}
