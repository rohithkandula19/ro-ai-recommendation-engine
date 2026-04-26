"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function WatchRedirect({ id }: { id: string }) {
  const router = useRouter();
  useEffect(() => {
    if (id && id !== "index") router.replace(`/browse/${id}`);
  }, [id, router]);
  return null;
}
