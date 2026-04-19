"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";

export function NotificationBell() {
  const [unread, setUnread] = useState(0);
  const { data } = useQuery({
    queryKey: ["notif-count"],
    queryFn: async () => (await api.get("/users/me/notifications?unread_only=true")).data,
    refetchInterval: 30000,
  });
  useEffect(() => { setUnread(data?.items?.length ?? 0); }, [data]);

  useWebSocket("/ws/notifications", (m: any) => {
    if (m.type === "notification") setUnread((n) => n + 1);
  });

  return (
    <Link href="/notifications" aria-label="notifications" className="relative hover:text-white">
      <span>🔔</span>
      {unread > 0 && (
        <span className="absolute -top-1 -right-2 rounded-full bg-brand text-[10px] font-bold px-1 min-w-[16px] h-4 flex items-center justify-center">
          {unread > 9 ? "9+" : unread}
        </span>
      )}
    </Link>
  );
}
