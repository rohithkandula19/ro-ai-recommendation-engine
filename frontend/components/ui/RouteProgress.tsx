"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

function Inner() {
  const pathname = usePathname();
  const sp = useSearchParams();
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
    setProgress(10);
    const a = setTimeout(() => setProgress(60), 120);
    const b = setTimeout(() => setProgress(95), 400);
    const done = setTimeout(() => { setProgress(100); setTimeout(() => setVisible(false), 250); }, 700);
    return () => { clearTimeout(a); clearTimeout(b); clearTimeout(done); };
  }, [pathname, sp]);

  if (!visible) return null;
  return (
    <div className="fixed top-0 left-0 right-0 h-0.5 bg-transparent z-[60] pointer-events-none">
      <div className="h-full bg-brand transition-all duration-200 shadow-[0_0_8px_#E50914]"
        style={{ width: `${progress}%` }} />
    </div>
  );
}

export function RouteProgress() {
  return <Suspense fallback={null}><Inner /></Suspense>;
}
