"use client";

import { useEffect, useState } from "react";

export function InstallPrompt() {
  const [deferred, setDeferred] = useState<any>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem("ro-install-dismissed")) { setDismissed(true); return; }
    const handler = (e: Event) => { e.preventDefault(); setDeferred(e); };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!deferred || dismissed) return null;

  async function install() {
    deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  }
  function close() {
    localStorage.setItem("ro-install-dismissed", "1");
    setDismissed(true);
  }

  return (
    <div className="fixed bottom-24 left-4 md:left-6 z-[55] max-w-sm rounded-lg bg-surface-elevated ring-1 ring-white/10 p-4 shadow-xl">
      <p className="text-sm">Install RO as an app for quicker access.</p>
      <div className="mt-2 flex gap-2 justify-end">
        <button onClick={close} className="text-xs text-white/50">Not now</button>
        <button onClick={install} className="text-xs rounded bg-brand px-3 py-1 font-semibold">Install</button>
      </div>
    </div>
  );
}
