"use client";

import { useParams } from "next/navigation";
import { ContentDetail } from "@/components/content/ContentDetail";

export default function ContentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = (params?.id || "") as string;
  if (!id) return null;
  return <ContentDetail id={id} />;
}
