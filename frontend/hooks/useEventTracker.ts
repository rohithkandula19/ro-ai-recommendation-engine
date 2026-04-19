"use client";

import { useCallback, useEffect, useRef } from "react";
import { eventQueue } from "@/lib/eventQueue";
import { useAuthStore } from "@/store/authStore";
import type { EventType, TrackedEvent } from "@/types";

function randomUUID(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function detectDevice(): string {
  if (typeof window === "undefined") return "unknown";
  const w = window.innerWidth;
  if (w < 640) return "mobile";
  if (w < 1024) return "tablet";
  return "desktop";
}

export function useEventTracker() {
  const sessionRef = useRef<string>(randomUUID());
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    eventQueue.start();
    return () => eventQueue.stop();
  }, []);

  const track = useCallback(
    (event_type: EventType, content_id?: string | null, value?: number | null) => {
      if (!user) return;
      const e: TrackedEvent = {
        user_id: user.id,
        content_id: content_id ?? null,
        event_type,
        value: value ?? null,
        session_id: sessionRef.current,
        device_type: detectDevice(),
      };
      eventQueue.track(e);
    },
    [user]
  );

  return { track, sessionId: sessionRef.current };
}
