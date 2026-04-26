"use client";

import { useState } from "react";
import { renderMarkdown } from "@/lib/chatMarkdown";
import { InlineTitleCard } from "./InlineTitleCard";
import { useToast } from "@/components/ui/Toast";

export interface Action { kind: string; content_id: string; label: string }
export interface ResolvedTitle { id: string; title: string; poster_url?: string | null; year?: number | null; type?: string | null }
export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  actions?: Action[];
  resolved?: ResolvedTitle[];
  streaming?: boolean;
}

interface Props {
  msg: ChatMsg;
  onFeedback?: (v: 1 | -1) => void;
  onRegenerate?: () => void;
  onAction?: (a: Action) => void;
  onSpeak?: () => void;
  isLast?: boolean;
}

export function Message({ msg, onFeedback, onRegenerate, onAction, onSpeak, isLast }: Props) {
  const toast = useToast();
  const [copied, setCopied] = useState(false);
  const isUser = msg.role === "user";

  async function copy() {
    try {
      await navigator.clipboard.writeText(msg.content);
      setCopied(true);
      toast.show("Copied", "success");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.show("Copy failed");
    }
  }

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} animate-[ro-fade-up_260ms_ease-out]`}>
      {!isUser && (
        <div className="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-brand to-brand-dark flex items-center justify-center text-[12px] font-black ring-1 ring-white/10">
          RO
        </div>
      )}
      <div className={`max-w-[78%] ${isUser ? "" : "flex-1"}`}>
        <div className={`rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed whitespace-pre-wrap break-words ${
          isUser ? "bg-brand text-white rounded-tr-sm" : "bg-white/[0.06] text-white/90 rounded-tl-sm ring-1 ring-white/5"
        }`}>
          <div>
            {renderMarkdown(msg.content)}
            {msg.streaming && (
              <span className="inline-block w-[2px] h-[1em] align-text-bottom bg-white/90 animate-pulse ml-0.5" />
            )}
          </div>
        </div>

        {msg.resolved && msg.resolved.length > 0 && (
          <div className="mt-2 flex flex-col gap-1.5">
            {msg.resolved.map((r) => (
              <InlineTitleCard key={r.id} id={r.id} title={r.title} posterUrl={r.poster_url} year={r.year} type={r.type} />
            ))}
          </div>
        )}

        {msg.actions && msg.actions.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {msg.actions.map((a, i) => (
              <button
                key={i}
                onClick={() => onAction?.(a)}
                className="text-xs font-medium rounded-full bg-white/10 hover:bg-brand hover:text-white px-3 py-1 transition-all lift-hover"
              >
                {a.label}
              </button>
            ))}
          </div>
        )}

        {!isUser && !msg.streaming && msg.content && (
          <div className="mt-1.5 flex items-center gap-1 text-xs text-white/40">
            <button onClick={() => onFeedback?.(1)} className="hover:text-emerald-400 p-1" title="Good reply">👍</button>
            <button onClick={() => onFeedback?.(-1)} className="hover:text-red-400 p-1" title="Bad reply">👎</button>
            <button onClick={copy} className="hover:text-white p-1" title="Copy">{copied ? "✓" : "⧉"}</button>
            {onSpeak && <button onClick={onSpeak} className="hover:text-white p-1" title="Speak">🔊</button>}
            {isLast && onRegenerate && (
              <button onClick={onRegenerate} className="hover:text-white p-1" title="Regenerate">↻</button>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 shrink-0 rounded-full bg-white/10 flex items-center justify-center text-[11px] font-bold ring-1 ring-white/10">
          You
        </div>
      )}
    </div>
  );
}
