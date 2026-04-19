"use client";

import { useParams } from "next/navigation";
import { RichContentDetail } from "@/components/content/RichContentDetail";

export default function ContentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = (params?.id || "") as string;
  if (!id) return null;
  return <RichContentDetail id={id} />;
}
