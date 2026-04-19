"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";

const KEY = "ro-consent-v1";

export function CookieBanner() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!localStorage.getItem(KEY)) setOpen(true);
  }, []);

  function accept(all: boolean) {
    localStorage.setItem(KEY, JSON.stringify({ analytics: all, marketing: all, personalization: true, ts: Date.now() }));
    setOpen(false);
  }

  if (!open) return null;
  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:w-96 z-[55] rounded-lg bg-surface-elevated ring-1 ring-white/10 shadow-2xl p-4 text-sm">
      <p className="text-white/80">
        We use essential cookies for sign-in and optional cookies for analytics. You can change this anytime in <a href="/security" className="underline">Security</a>.
      </p>
      <div className="mt-3 flex gap-2 justify-end">
        <Button variant="ghost" onClick={() => accept(false)}>Essential only</Button>
        <Button onClick={() => accept(true)}>Accept all</Button>
      </div>
    </div>
  );
}
