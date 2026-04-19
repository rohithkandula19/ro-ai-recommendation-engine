"use client";

import { Modal } from "@/components/ui/Modal";
import { useExplain } from "@/hooks/useUniqueFeatures";

interface Props {
  contentId: string | null;
  open: boolean;
  onClose: () => void;
}

export function WhyCard({ contentId, open, onClose }: Props) {
  const { data, isLoading } = useExplain(contentId);

  return (
    <Modal open={open} onClose={onClose}>
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Why this pick</h2>
        {isLoading && <p className="text-white/60">Loading…</p>}
        {data?.ai_summary && (
          <div className="rounded-md bg-brand/10 border border-brand/30 p-3 text-sm">
            <span className="text-xs uppercase text-brand mr-2">AI</span>
            {data.ai_summary}
          </div>
        )}
        {data && (
          <>
            <p className="text-sm text-white/70">{data.dominant_reason}</p>
            <ul className="space-y-3">
              {data.signals.map((s) => (
                <li key={s.name}>
                  <div className="flex justify-between text-xs text-white/70">
                    <span className="capitalize">{s.name.replace(/_/g, " ")}</span>
                    <span>{Math.round(s.value * 100)}%</span>
                  </div>
                  <div className="mt-1 h-1.5 w-full rounded bg-white/10 overflow-hidden">
                    <div className="h-full bg-brand" style={{ width: `${s.value * 100}%` }} />
                  </div>
                  <p className="mt-1 text-xs text-white/50">{s.description}</p>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </Modal>
  );
}
