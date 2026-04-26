"use client";
import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAuthStore } from "@/store/authStore";

interface Msg { id: number; sender_id: string; recipient_id: string; body: string; created_at: string }

export default function DMPage({ params }: { params: { id: string } }) {
  const otherId = params?.id as string;
  const me = useAuthStore((s) => s.user);
  const qc = useQueryClient();
  const [input, setInput] = useState("");
  const [otherTyping, setOtherTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const { data } = useQuery<{ items: Msg[] }>({
    queryKey: ["dm", otherId],
    queryFn: async () => (await api.get(`/messages/with/${otherId}`)).data,
    enabled: !!otherId,
    refetchInterval: 5000,
  });

  const { send } = useWebSocket(
    otherId ? `/ws/chat-typing/${otherId}` : null,
    (m: any) => { if (m.type === "typing" && m.user_id === otherId) setOtherTyping(m.is_typing); }
  );

  useEffect(() => { scrollRef.current?.scrollTo({ top: 1e9 }); }, [data]);

  async function submit() {
    if (!input.trim()) return;
    await api.post("/messages", { recipient_id: otherId, body: input });
    setInput("");
    send({ is_typing: false });
    qc.invalidateQueries({ queryKey: ["dm", otherId] });
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-6 h-[calc(100vh-120px)] flex flex-col">
      <h1 className="text-xl font-bold mb-3">Conversation</h1>
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 rounded-md bg-surface-elevated ring-1 ring-white/10 p-4">
        {data?.items.map((m) => {
          const mine = m.sender_id === me?.id;
          return (
            <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm ${mine ? "bg-brand text-white" : "bg-white/10"}`}>
                {m.body}
                <div className="mt-1 text-[10px] opacity-60">{new Date(m.created_at).toLocaleTimeString()}</div>
              </div>
            </div>
          );
        })}
        {otherTyping && <div className="text-xs text-white/50 italic">typing…</div>}
      </div>
      <div className="mt-3 flex gap-2">
        <input value={input}
          onChange={(e) => { setInput(e.target.value); send({ is_typing: e.target.value.length > 0 }); }}
          onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
          placeholder="Message…"
          className="flex-1 rounded bg-black/60 px-3 py-2 text-sm ring-1 ring-white/10" />
        <button onClick={submit} className="rounded bg-brand px-4 text-sm font-semibold">Send</button>
      </div>
    </div>
  );
}
