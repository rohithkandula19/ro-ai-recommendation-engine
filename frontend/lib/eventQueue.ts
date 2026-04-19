import { api } from "./api";
import type { TrackedEvent } from "@/types";

const MAX_BATCH = 10;
const FLUSH_MS = 5000;

class EventQueue {
  private queue: TrackedEvent[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;

  start() {
    if (this.timer || typeof window === "undefined") return;
    this.timer = setInterval(() => this.flush(), FLUSH_MS);
    window.addEventListener("beforeunload", () => this.flushBeacon());
    window.addEventListener("pagehide", () => this.flushBeacon());
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  track(e: TrackedEvent) {
    this.queue.push({ ...e, timestamp: e.timestamp || new Date().toISOString() });
    if (this.queue.length >= MAX_BATCH) {
      this.flush();
    }
  }

  async flush() {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0, this.queue.length);
    try {
      await api.post("/events/ingest", { events: batch });
    } catch {
      this.queue.unshift(...batch);
    }
  }

  flushBeacon() {
    if (this.queue.length === 0 || typeof navigator === "undefined") return;
    const body = JSON.stringify({ events: this.queue });
    const url = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/events/ingest";
    const blob = new Blob([body], { type: "application/json" });
    navigator.sendBeacon(url, blob);
    this.queue = [];
  }
}

export const eventQueue = new EventQueue();
