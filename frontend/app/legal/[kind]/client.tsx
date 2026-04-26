"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function LegalPage({ params }: { params: { kind: string } }) {
  const kind = params?.kind as string;
  const { data } = useQuery({
    queryKey: ["legal", kind],
    queryFn: async () => (await api.get(`/legal/${kind}`)).data,
    enabled: !!kind,
  });
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <h1 className="text-3xl font-extrabold capitalize">{kind}</h1>
      <p className="mt-6 whitespace-pre-wrap text-white/80">{data?.text ?? "…"}</p>
    </div>
  );
}
