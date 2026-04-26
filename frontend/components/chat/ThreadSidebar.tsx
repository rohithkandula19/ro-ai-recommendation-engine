"use client";

import { useEffect, useState } from "react";

export interface Thread {
  id: string;
  title: string;
  updated_at: number;
  turn_count: number;
}

const KEY = "ro:chat:threads";

export function loadThreads(): Thread[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const v = JSON.parse(raw);
    if (!Array.isArray(v)) return [];
    return v;
  } catch { return []; }
}

export function saveThreads(list: Thread[]) {
  try { window.localStorage.setItem(KEY, JSON.stringify(list)); } catch {}
}

export function newThread(): Thread {
  return { id: crypto.randomUUID(), title: "New chat", updated_at: Date.now(), turn_count: 0 };
}

interface Props {
  active: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
  threads: Thread[];
}

export function ThreadSidebar({ active, onSelect, onNew, onRename, onDelete, threads }: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  return (
    <aside className="w-64 shrink-0 bg-black/40 ring-1 ring-white/5 flex flex-col h-full">
      <div className="p-3 border-b border-white/10">
        <button
          onClick={onNew}
          className="w-full rounded-lg bg-brand hover:bg-brand-dark text-white text-sm font-semibold py-2 px-3 flex items-center justify-center gap-2 lift-hover"
        >
          <span className="text-lg leading-none">+</span> New chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {threads.length === 0 && (
          <div className="text-xs text-white/40 p-3">No saved chats yet.</div>
        )}
        {threads.map((t) => {
          const isActive = t.id === active;
          const isEditing = editing === t.id;
          return (
            <div
              key={t.id}
              className={`group/thread relative rounded-lg px-3 py-2 text-sm cursor-pointer ${
                isActive ? "bg-white/10 ring-1 ring-white/15" : "hover:bg-white/[0.06]"
              }`}
              onClick={() => !isEditing && onSelect(t.id)}
            >
              {isEditing ? (
                <input
                  autoFocus
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onBlur={() => { onRename(t.id, draft.trim() || t.title); setEditing(null); }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") { onRename(t.id, draft.trim() || t.title); setEditing(null); }
                    if (e.key === "Escape") setEditing(null);
                  }}
                  className="w-full bg-black/40 rounded px-2 py-1 text-sm ring-1 ring-white/20 outline-none"
                />
              ) : (
                <>
                  <div className="truncate text-white/90">{t.title}</div>
                  <div className="text-[10px] text-white/40 mt-0.5">
                    {t.turn_count > 0 ? `${t.turn_count} msgs · ` : ""}{new Date(t.updated_at).toLocaleDateString()}
                  </div>
                </>
              )}
              {!isEditing && (
                <div className="absolute right-1.5 top-1.5 flex gap-0.5 opacity-0 group-hover/thread:opacity-100 transition">
                  <button
                    onClick={(e) => { e.stopPropagation(); setEditing(t.id); setDraft(t.title); }}
                    className="p-1 rounded hover:bg-white/10 text-xs" aria-label="rename">✎</button>
                  <button
                    onClick={(e) => { e.stopPropagation(); if (confirm("Delete this chat?")) onDelete(t.id); }}
                    className="p-1 rounded hover:bg-red-500/30 text-xs" aria-label="delete">✕</button>
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="p-3 border-t border-white/10 text-[10px] text-white/40">
        <div className="font-semibold text-white/60 mb-1">Slash commands</div>
        <code className="block">/decisive · /surprise · /stats</code>
        <code className="block">/mood tense · /new · /export</code>
      </div>
    </aside>
  );
}
