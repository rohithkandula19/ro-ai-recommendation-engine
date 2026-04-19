"use client";

import { useEffect, useRef, useState } from "react";

interface Props { onTranscript: (text: string) => void }

export function VoiceMic({ onTranscript }: Props) {
  const [recording, setRecording] = useState(false);
  const [supported, setSupported] = useState(true);
  const recRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-US";
    rec.onresult = (e: any) => {
      const text = Array.from(e.results).map((r: any) => r[0].transcript).join(" ");
      onTranscript(text);
    };
    rec.onend = () => setRecording(false);
    rec.onerror = () => setRecording(false);
    recRef.current = rec;
  }, [onTranscript]);

  if (!supported) return null;

  function toggle() {
    if (recording) { recRef.current?.stop(); return; }
    try { recRef.current?.start(); setRecording(true); } catch {}
  }

  return (
    <button type="button" onClick={toggle} aria-label="voice input"
      className={`rounded-full w-8 h-8 flex items-center justify-center text-base ${
        recording ? "bg-red-500 animate-pulse" : "bg-white/10 hover:bg-white/20"
      }`}>
      🎤
    </button>
  );
}
