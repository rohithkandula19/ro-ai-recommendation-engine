"use client";

import { useEffect, useState } from "react";

const SESSION_KEY = "ro-intro-played";

export function RoIntro({ onDone }: { onDone?: () => void }) {
  const [stage, setStage] = useState<"waiting" | "playing" | "done">("waiting");

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SESSION_KEY)) {
      setStage("done");
      onDone?.();
      return;
    }
    setStage("playing");
    const t1 = setTimeout(() => setStage("done"), 2400);
    const t2 = setTimeout(() => onDone?.(), 2700);
    try { sessionStorage.setItem(SESSION_KEY, "1"); } catch {}
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onDone]);

  if (stage === "done" || stage === "waiting") return null;

  return (
    <div className="fixed inset-0 z-[70] bg-black flex items-center justify-center" aria-hidden="true">
      {/* Ambient red glow */}
      <div className="absolute inset-0 pointer-events-none opacity-0 animate-[ro-glow_2400ms_ease-out_forwards]"
        style={{
          background: "radial-gradient(circle at 50% 50%, rgba(229,9,20,0.35), transparent 55%)",
        }}
      />

      {/* Logo */}
      <svg viewBox="0 0 420 180" className="w-[min(86vw,720px)] drop-shadow-[0_0_30px_rgba(229,9,20,0.55)]">
        <defs>
          <linearGradient id="ro-grad" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#ff2b36" />
            <stop offset="0.5" stopColor="#E50914" />
            <stop offset="1" stopColor="#960510" />
          </linearGradient>
          <filter id="ro-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* R — stroke-draw animation */}
        <path
          d="M 70 30 L 70 150 M 70 30 L 140 30 Q 180 30 180 65 Q 180 100 140 100 L 70 100 M 140 100 L 185 150"
          fill="none"
          stroke="url(#ro-grad)"
          strokeWidth="14"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="700"
          strokeDashoffset="700"
          filter="url(#ro-glow)"
          style={{ animation: "ro-stroke 1.1s 0.15s ease-out forwards" }}
        />

        {/* O — circle draw + pulse */}
        <circle
          cx="300" cy="90" r="62"
          fill="none"
          stroke="url(#ro-grad)"
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray="400"
          strokeDashoffset="400"
          filter="url(#ro-glow)"
          style={{ animation: "ro-stroke 1.1s 0.55s ease-out forwards, ro-pulse 1.2s 1.4s ease-out" }}
        />

        {/* Tagline */}
        <text x="210" y="174" textAnchor="middle"
          fill="#ffffff" fillOpacity="0"
          fontSize="11" fontWeight="600" letterSpacing="4"
          style={{ animation: "ro-fade 0.6s 1.6s ease-out forwards" }}>
          A I   R E C O M M E N D A T I O N   E N G I N E
        </text>
      </svg>

      <style>{`
        @keyframes ro-stroke {
          to { stroke-dashoffset: 0; }
        }
        @keyframes ro-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        @keyframes ro-glow {
          0% { opacity: 0; }
          40% { opacity: 1; }
          100% { opacity: 0; }
        }
        @keyframes ro-fade {
          to { fill-opacity: 0.75; }
        }
      `}</style>
    </div>
  );
}
