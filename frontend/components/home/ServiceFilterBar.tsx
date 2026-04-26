"use client";

import Link from "next/link";
import { useServiceFilter } from "@/hooks/useServiceFilter";

export function ServiceFilterBar() {
  const { onlyMine, setOnlyMine, subscriptions } = useServiceFilter();

  return (
    <div className="mx-6 mt-4 flex flex-wrap items-center gap-3 rounded-lg bg-white/[0.03] ring-1 ring-white/10 px-4 py-2.5 text-sm">
      <span className="text-white/60">
        {subscriptions.length > 0
          ? `You subscribe to ${subscriptions.length} service${subscriptions.length === 1 ? "" : "s"}`
          : "Tell RO what you subscribe to"}
      </span>

      {subscriptions.length > 0 ? (
        <label className="ml-auto inline-flex items-center gap-2 cursor-pointer">
          <span className="text-white/70">Only on my services</span>
          <button
            type="button"
            role="switch"
            aria-checked={onlyMine}
            onClick={() => setOnlyMine(!onlyMine)}
            className={`relative h-5 w-9 rounded-full transition-colors ${onlyMine ? "bg-brand" : "bg-white/20"}`}
          >
            <span className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform ${onlyMine ? "translate-x-4" : ""}`} />
          </button>
        </label>
      ) : (
        <Link href="/profile" className="ml-auto text-brand hover:underline">Set up →</Link>
      )}
    </div>
  );
}
