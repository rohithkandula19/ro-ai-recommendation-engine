"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api, getAccessToken } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useToast } from "@/components/ui/Toast";
import { Message, type ChatMsg, type Action, type ResolvedTitle } from "./Message";
import { ThinkingBadge } from "./ThinkingBadge";
import { ThreadSidebar, loadThreads, saveThreads, newThread, type Thread } from "./ThreadSidebar";
import { VoiceMic } from "./VoiceMic";
import { SLASH_COMMANDS, parseSlash } from "@/lib/slashCommands";
import { extractCandidateTitles } from "@/lib/chatMarkdown";

const KEY_MSGS = (tid: string) => `ro:chat:msgs:${tid}`;

function loadMessages(tid: string): ChatMsg[] {
  try {
    const raw = window.localStorage.getItem(KEY_MSGS(tid));
    if (!raw) return [];
    const v = JSON.parse(raw);
    return Array.isArray(v) ? v : [];
  } catch { return []; }
}
function saveMessages(tid: string, msgs: ChatMsg[]) {
  try { window.localStorage.setItem(KEY_MSGS(tid), JSON.stringify(msgs.slice(-100))); } catch {}
}
function speak(text: string) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.slice(0, 600));
  u.rate = 1.05; window.speechSynthesis.speak(u);
}

export function ChatPage() {
  const user = useAuthStore((s) => s.user);
  const toast = useToast();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [suggestOpen, setSuggestOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const list = loadThreads();
    if (list.length === 0) {
      const t = newThread();
      saveThreads([t]);
      setThreads([t]);
      setActiveId(t.id);
    } else {
      setThreads(list);
      setActiveId(list[0].id);
    }
  }, []);

  useEffect(() => {
    if (!activeId) return;
    setMsgs(loadMessages(activeId));
  }, [activeId]);

  useEffect(() => {
    if (!activeId) return;
    saveMessages(activeId, msgs);
    const cur = threads.find((t) => t.id === activeId);
    if (cur) {
      const updated = threads.map((t) =>
        t.id === activeId ? { ...t, turn_count: msgs.length, updated_at: Date.now(),
          title: t.title === "New chat" && msgs[0]?.role === "user" ? msgs[0].content.slice(0, 48) : t.title } : t
      );
      if (JSON.stringify(updated) !== JSON.stringify(threads)) {
        setThreads(updated);
        saveThreads(updated);
      }
    }
  }, [msgs, activeId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, thinking]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }, [input]);

  const isActiveEmpty = msgs.length === 0;

  function handleNew() {
    const t = newThread();
    const next = [t, ...threads];
    setThreads(next); saveThreads(next); setActiveId(t.id); setMsgs([]);
  }
  function handleRename(id: string, title: string) {
    const next = threads.map((t) => t.id === id ? { ...t, title } : t);
    setThreads(next); saveThreads(next);
  }
  function handleDelete(id: string) {
    const next = threads.filter((t) => t.id !== id);
    try { window.localStorage.removeItem(KEY_MSGS(id)); } catch {}
    if (next.length === 0) {
      const t = newThread();
      setThreads([t]); saveThreads([t]); setActiveId(t.id); setMsgs([]);
    } else {
      setThreads(next); saveThreads(next);
      if (activeId === id) { setActiveId(next[0].id); setMsgs(loadMessages(next[0].id)); }
    }
  }

  async function resolveTitles(text: string): Promise<ResolvedTitle[]> {
    const candidates = extractCandidateTitles(text);
    if (candidates.length === 0) return [];
    const out: ResolvedTitle[] = [];
    const seen = new Set<string>();
    for (const q of candidates.slice(0, 5)) {
      try {
        const r = await api.get("/search", { params: { q, limit: 1 } });
        const hit = r.data?.items?.[0];
        if (hit?.id && !seen.has(hit.id)) {
          seen.add(hit.id);
          out.push({ id: hit.id, title: hit.title, poster_url: hit.thumbnail_url, year: hit.release_year, type: hit.type });
        }
      } catch {}
    }
    return out;
  }

  async function handleSlash(cmd: string, args: string): Promise<boolean> {
    switch (cmd) {
      case "/new": handleNew(); return true;
      case "/clear":
        try { await api.post("/chat/clear"); } catch {}
        setMsgs([]); toast.show("Memory cleared", "success"); return true;
      case "/export": {
        const md = msgs.map((m) => `**${m.role === "user" ? "You" : "RO"}:** ${m.content}`).join("\n\n");
        const blob = new Blob([md], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = `ro-chat-${Date.now()}.md`; a.click();
        URL.revokeObjectURL(url); return true;
      }
      case "/stats": await send("summarize my taste DNA in one paragraph"); return true;
      case "/surprise": await send("surprise me — one great pick I wouldn't expect"); return true;
      case "/mood": await send(`mood: ${args || "balanced"} — give me 3 picks`); return true;
      case "/decisive": await send(args || "just pick one for tonight", "decisive"); return true;
      default: toast.show(`Unknown command ${cmd}`); return true;
    }
  }

  async function send(text: string, mode: "stream" | "decisive" | "agent" = "stream") {
    const message = text.trim();
    if (!message || streaming) return;

    const slash = parseSlash(message);
    if (slash) {
      if (await handleSlash(slash.cmd, slash.args)) return;
    }

    setInput(""); setSuggestOpen(false);
    const userMsg: ChatMsg = { role: "user", content: message };
    const asstMsg: ChatMsg = { role: "assistant", content: "", streaming: true };
    setMsgs((m) => [...m, userMsg, asstMsg]);
    setThinking(true);
    setStreaming(true);

    const ac = new AbortController();
    abortRef.current = ac;

    try {
      const token = getAccessToken();
      const endpoint = mode === "decisive" ? "/chat/decisive" : mode === "agent" ? "/chat/agent" : "/chat/stream";
      const resp = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(mode === "decisive" ? { context: message } : { message }),
        signal: ac.signal,
      });

      if (mode === "stream") {
        if (!resp.ok || !resp.body) throw new Error("chat fail");
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let acc = "";
        let gotFirstToken = false;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          acc += decoder.decode(value, { stream: true });
          if (!gotFirstToken && acc.length > 0) {
            gotFirstToken = true;
            setThinking(false);
          }
          setMsgs((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: acc, streaming: true }; return n; });
        }
        const resolved = await resolveTitles(acc);
        setMsgs((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: acc, resolved, streaming: false }; return n; });
      } else if (mode === "agent") {
        const data = await resp.json();
        const resolved = await resolveTitles(data.reply ?? "");
        setMsgs((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: data.reply ?? "", actions: data.actions, resolved, streaming: false }; return n; });
      } else {
        const data = await resp.json();
        const reply = `**${data.title}**\n\n${data.verdict}`;
        const resolved: ResolvedTitle[] = data.id ? [{ id: data.id, title: data.title, poster_url: data.thumbnail_url, year: data.release_year, type: data.type }] : [];
        setMsgs((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: reply, actions: [{ kind: "play", content_id: data.id, label: `▶ Watch ${data.title}` }], resolved, streaming: false }; return n; });
      }
    } catch (e: any) {
      if (e?.name !== "AbortError") {
        setMsgs((t) => { const n = t.slice(); n[n.length - 1] = { role: "assistant", content: "Connection hiccup. Try again.", streaming: false }; return n; });
      } else {
        setMsgs((t) => { const n = t.slice(); n[n.length - 1] = { ...n[n.length - 1], streaming: false }; return n; });
      }
    } finally {
      setStreaming(false); setThinking(false); abortRef.current = null;
    }
  }

  async function regenerate() {
    const lastUser = [...msgs].reverse().find((m) => m.role === "user");
    if (!lastUser) return;
    setMsgs((m) => m.slice(0, -1));
    await send(lastUser.content);
  }

  function execAction(a: Action) {
    if (a.kind === "play") { window.location.href = `/watch/${a.content_id}`; return; }
    if (a.kind === "view_details") { window.location.href = `/browse/${a.content_id}`; return; }
    api.post("/chat/action", { intent: a.kind, content_id: a.content_id }).catch(() => {});
  }

  async function feedback(idx: number, v: 1 | -1) {
    const assistant = msgs[idx]?.content || "";
    const userMsg = msgs[idx - 1]?.role === "user" ? msgs[idx - 1].content : null;
    try {
      await api.post("/chat/feedback", { turn_index: idx, assistant_message: assistant, user_message: userMsg, feedback: v });
      toast.show(v === 1 ? "Thanks — noted" : "Got it — will adjust", "success");
    } catch {}
  }

  const slashMatches = useMemo(() => {
    if (!input.startsWith("/")) return [];
    const q = input.toLowerCase();
    return SLASH_COMMANDS.filter((c) => c.cmd.startsWith(q)).slice(0, 6);
  }, [input]);

  if (!user) return (
    <div className="mx-auto max-w-md p-12 text-center text-white/70">
      Sign in to use RO chat.
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-68px)] overflow-hidden bg-[radial-gradient(ellipse_at_top,_rgba(229,9,20,0.06),_transparent_60%)]">
      <ThreadSidebar
        active={activeId}
        threads={threads}
        onSelect={(id) => setActiveId(id)}
        onNew={handleNew}
        onRename={handleRename}
        onDelete={handleDelete}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between px-6 py-3 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand to-brand-dark flex items-center justify-center text-sm font-black brand-pulse">RO</div>
            <div>
              <div className="font-bold">Ask RO</div>
              <div className="text-[11px] text-white/50">Remembers your DNA · type <code className="bg-white/10 px-1 rounded">/</code> for commands</div>
            </div>
          </div>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {isActiveEmpty && (
            <div className="max-w-2xl mx-auto py-16 text-center space-y-6 animate-[ro-fade-up_420ms_ease-out]">
              <div className="inline-flex w-16 h-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand to-brand-dark text-2xl font-black brand-pulse">RO</div>
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight">Hi {user.display_name.split(" ")[0]}.</h1>
                <p className="mt-2 text-white/60">What do you feel like watching?</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-xl mx-auto">
                {[
                  "Something slow and thoughtful for tonight",
                  "A 90-minute thriller I haven't seen",
                  "Summarize my taste",
                  "Surprise me with a hidden gem",
                ].map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-left text-sm rounded-lg bg-white/[0.04] ring-1 ring-white/10 hover:bg-white/[0.08] lift-hover px-4 py-3 text-white/80"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {msgs.map((m, i) => (
            <Message
              key={i}
              msg={m}
              isLast={i === msgs.length - 1}
              onAction={execAction}
              onFeedback={(v) => feedback(i, v)}
              onSpeak={() => speak(m.content)}
              onRegenerate={regenerate}
            />
          ))}

          {thinking && (
            <div className="flex gap-3 animate-[ro-fade-up_200ms_ease-out]">
              <div className="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-brand to-brand-dark flex items-center justify-center text-[12px] font-black">RO</div>
              <ThinkingBadge />
            </div>
          )}
        </div>

        <div className="border-t border-white/10 px-6 py-4">
          <form
            onSubmit={(e) => { e.preventDefault(); send(input); }}
            className="relative flex items-end gap-2 max-w-3xl mx-auto"
          >
            {suggestOpen && slashMatches.length > 0 && (
              <div className="absolute bottom-full left-0 mb-2 w-80 rounded-lg bg-surface-elevated ring-1 ring-white/10 shadow-2xl py-1 animate-[ro-fade-up_160ms_ease-out]">
                {slashMatches.map((c) => (
                  <button
                    key={c.cmd}
                    type="button"
                    onClick={() => { setInput(c.cmd + (c.hint ? " " : "")); textareaRef.current?.focus(); }}
                    className="block w-full text-left px-3 py-2 hover:bg-white/10 transition"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <code className="text-sm text-brand font-semibold">{c.cmd}</code>
                      {c.hint && <span className="text-[10px] text-white/40">&lt;{c.hint}&gt;</span>}
                    </div>
                    <div className="text-xs text-white/60">{c.desc}</div>
                  </button>
                ))}
              </div>
            )}

            <VoiceMic onTranscript={(t) => setInput((cur) => (cur ? cur + " " : "") + t)} />

            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => { setInput(e.target.value); setSuggestOpen(e.target.value.startsWith("/")); }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
                  if (e.key === "Escape") setSuggestOpen(false);
                }}
                disabled={streaming}
                placeholder="Ask RO anything · Shift+Enter for newline · / for commands"
                rows={1}
                className="w-full resize-none rounded-xl bg-black/40 ring-1 ring-white/10 focus:ring-brand px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition-shadow max-h-[180px]"
              />
            </div>

            {streaming ? (
              <button
                type="button"
                onClick={() => abortRef.current?.abort()}
                className="h-11 rounded-xl bg-white/10 hover:bg-red-500/80 px-4 text-sm font-semibold transition"
              >
                Stop
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => send(input || "take the best action for me right now", "agent")}
                  disabled={streaming}
                  className="h-11 rounded-xl bg-amber-500/80 hover:bg-amber-400 text-black px-3 text-sm font-bold disabled:opacity-40 lift-hover"
                  title="Agent mode — let RO act"
                >
                  ⚡
                </button>
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="h-11 rounded-xl bg-brand hover:bg-brand-dark px-5 text-sm font-bold text-white disabled:opacity-40 lift-hover"
                >
                  Send
                </button>
              </>
            )}
          </form>
        </div>
      </main>
    </div>
  );
}
