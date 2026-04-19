"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

type ToastKind = "info" | "success" | "error";
interface Toast { id: number; kind: ToastKind; message: string }
interface Ctx { show: (message: string, kind?: ToastKind) => void }

const ToastCtx = createContext<Ctx>({ show: () => {} });
let _id = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const show = useCallback((message: string, kind: ToastKind = "info") => {
    const id = ++_id;
    setItems((x) => [...x, { id, kind, message }]);
    setTimeout(() => setItems((x) => x.filter((t) => t.id !== id)), 2600);
  }, []);

  return (
    <ToastCtx.Provider value={{ show }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 space-y-2 pointer-events-none">
        {items.map((t) => (
          <div key={t.id}
            className={`pointer-events-auto rounded-md px-4 py-2 text-sm shadow-lg ring-1 ring-white/10 ${
              t.kind === "error" ? "bg-red-900/90 text-red-100" :
              t.kind === "success" ? "bg-emerald-900/90 text-emerald-100" :
              "bg-surface-elevated text-white"
            }`}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export function useToast() { return useContext(ToastCtx); }
