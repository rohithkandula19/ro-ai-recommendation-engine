"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";

interface Action { kind: string; content_id: string; label: string }

export function AgentActions({ actions }: { actions: Action[] }) {
  const toast = useToast();
  if (!actions?.length) return null;

  async function exec(a: Action) {
    try {
      if (a.kind === "play") { window.location.href = `/watch/${a.content_id}`; return; }
      if (a.kind === "view_details") { window.location.href = `/browse/${a.content_id}`; return; }
      await api.post("/chat/action", {
        intent: a.kind === "add_to_list" ? "add_to_list"
              : a.kind === "rate" ? "rate"
              : a.kind === "mark_watched" ? "mark_watched"
              : "add_to_list",
        content_id: a.content_id,
      });
      toast.show(`✓ ${a.label}`, "success");
    } catch {
      toast.show("Couldn't complete that", "error");
    }
  }

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {actions.slice(0, 4).map((a, i) => (
        <button key={i} onClick={() => exec(a)}
          className="text-xs rounded-full bg-white/10 hover:bg-brand hover:text-white px-3 py-1 transition">
          {a.label}
        </button>
      ))}
    </div>
  );
}
