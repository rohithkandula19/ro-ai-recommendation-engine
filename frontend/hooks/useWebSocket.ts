"use client";

import { useEffect, useRef, useState } from "react";
import { getAccessToken } from "@/lib/api";

export function useWebSocket(path: string | null, onMessage?: (data: any) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!path) return;
    const token = getAccessToken();
    if (!token) return;
    const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/^http/, "ws");
    const sep = path.includes("?") ? "&" : "?";
    const url = `${base}${path}${sep}token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMessage?.(data);
      } catch {}
    };
    return () => { try { ws.close(); } catch {} };
  }, [path, onMessage]);

  const send = (data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };

  return { connected, send };
}
