"use client";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function WatchPartyRoom({ room }: { room: string }) {
  const sp = useSearchParams();
  const contentId = sp?.get("content") || "";
  const [chat, setChat] = useState<{ user: string; text: string }[]>([]);
  const [msg, setMsg] = useState("");
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const { connected, send } = useWebSocket(
    room ? `/ws/party/${room}` : null,
    (m: any) => {
      if (m.type === "state" && videoRef.current) {
        if (Math.abs(videoRef.current.currentTime - m.position) > 1.5) {
          videoRef.current.currentTime = m.position;
        }
        if (m.is_playing) videoRef.current.play().catch(() => {});
        else videoRef.current.pause();
      } else if (m.type === "chat") {
        setChat((c) => [...c, { user: m.user_id.slice(0, 8), text: m.text }]);
      } else if (m.type === "join" || m.type === "leave") {
        setChat((c) => [...c, { user: "system", text: `user ${m.user_id.slice(0, 8)} ${m.type === "join" ? "joined" : "left"}` }]);
      }
    }
  );

  function sendChat() {
    if (!msg.trim()) return;
    send({ type: "chat", text: msg });
    setMsg("");
  }

  function emitState(position: number, is_playing: boolean) {
    send({ type: "state", position, is_playing });
  }

  return (
    <div className="grid md:grid-cols-[1fr_360px] gap-4 px-4 py-4 h-[calc(100vh-80px)]">
      <div className="relative bg-black">
        <span className={`absolute top-2 right-2 z-10 text-xs px-2 py-0.5 rounded ${connected ? "bg-emerald-500" : "bg-red-500"}`}>
          {connected ? "LIVE" : "disconnected"}
        </span>
        <div className="absolute top-2 left-2 z-10 text-xs bg-black/60 px-2 py-0.5 rounded">Room: {room}</div>
        <video ref={videoRef} src="https://www.w3schools.com/html/mov_bbb.mp4"
          className="w-full h-full"
          onPlay={() => videoRef.current && emitState(videoRef.current.currentTime, true)}
          onPause={() => videoRef.current && emitState(videoRef.current.currentTime, false)}
          onSeeked={() => videoRef.current && emitState(videoRef.current.currentTime, !videoRef.current.paused)}
          controls
        />
      </div>
      <aside className="rounded-md bg-surface-elevated ring-1 ring-white/10 p-3 flex flex-col">
        <h3 className="font-semibold text-sm mb-2">Live chat</h3>
        <div className="flex-1 overflow-y-auto space-y-1 text-sm pb-2">
          {chat.map((c, i) => (
            <div key={i} className="text-sm">
              <span className={`text-xs ${c.user === "system" ? "text-white/40" : "text-brand"}`}>{c.user}</span>
              <span className="ml-2">{c.text}</span>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input value={msg} onChange={(e) => setMsg(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") sendChat(); }}
            placeholder="say something…"
            className="flex-1 rounded bg-black/60 px-2 py-1 text-sm ring-1 ring-white/10" />
          <button onClick={sendChat} className="rounded bg-brand px-3 text-sm">Send</button>
        </div>
      </aside>
    </div>
  );
}
