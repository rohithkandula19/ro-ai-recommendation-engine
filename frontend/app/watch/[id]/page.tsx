"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function WatchPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  useEffect(() => {
    if (params?.id) router.replace(`/browse/${params.id}`);
  }, [params?.id, router]);
  return null;
}
