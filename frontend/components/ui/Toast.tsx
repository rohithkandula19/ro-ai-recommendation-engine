"use client";

import { createContext, useCallback, useContext, useState } from "react";

type ToastKind = "info" | "success" | "error";
interface Toast { id: number; kind: ToastKind; message: string }
interface Ctx { show: (message: string, kind?: ToastKind) => void }

const ToastCtx = createContext<Ctx>({ show: () => {} });
let _id = 0;

const ICON: Record<ToastKind, string> = { info: "•", success: "✓", error: "!" };

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const show = useCallback((message: string, kind: ToastKind = "info") => {
    const id = ++_id;
    setItems((x) => [...x.slice(-2), { id, kind, message }]);
    setTimeout(() => setItems((x) => x.filter((t) => t.id !== id)), 2800);
  }, []);

  return (
    <ToastCtx.Provider value={{ show }}>
      {children}
      <div className="fixed bottom-24 right-6 z-50 flex flex-col gap-2 pointer-events-none md:bottom-6">
        {items.map((t) => (
          <div key={t.id}
            role="status"
            className={`pointer-events-auto flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium shadow-2xl ring-1 backdrop-blur-lg transition-all
              animate-[ro-fade-up_200ms_ease-out] ${
              t.kind === "error"
                ? "bg-red-950/95 text-red-100 ring-red-500/30"
                : t.kind === "success"
                ? "bg-emerald-950/95 text-emerald-100 ring-emerald-500/30"
                : "bg-surface-elevated/95 text-white ring-white/10"
            }`}>
            <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
              t.kind === "error" ? "bg-red-500 text-white" :
              t.kind === "success" ? "bg-emerald-500 text-black" :
              "bg-white/20"
            }`}>{ICON[t.kind]}</span>
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast() { return useContext(ToastCtx); }
