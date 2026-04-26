"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useEventTracker } from "@/hooks/useEventTracker";

type Offer = {
  provider: string;
  provider_logo: string | null;
  deep_link: string;
  price: number | null;
  currency: string | null;
  quality: string | null;
};

type Availability = {
  content_id: string;
  region: string;
  offers: { stream?: Offer[]; rent?: Offer[]; buy?: Offer[]; free?: Offer[] };
};

const LABELS: Record<string, string> = {
  stream: "Stream with subscription",
  free: "Watch free",
  rent: "Rent",
  buy: "Buy",
};

export function ProviderGrid({ contentId, region = "US" }: { contentId: string; region?: string }) {
  const { track } = useEventTracker();
  const { data, isLoading } = useQuery<Availability>({
    queryKey: ["availability", contentId, region],
    queryFn: async () => (await api.get(`/availability/${contentId}?region=${region}`)).data,
    enabled: !!contentId,
  });

  if (isLoading) {
    return <div className="h-20 rounded-lg bg-white/5 shimmer" />;
  }

  const sections = (["stream", "free", "rent", "buy"] as const).filter(
    (k) => (data?.offers[k]?.length ?? 0) > 0,
  );

  if (sections.length === 0) {
    return (
      <div className="rounded-lg ring-1 ring-white/10 bg-white/[0.03] p-4 text-sm text-white/70">
        No streaming availability found in your region yet. Try a different region or check back later.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sections.map((key) => (
        <div key={key}>
          <div className="text-xs uppercase tracking-wider text-white/50 mb-2">{LABELS[key]}</div>
          <div className="flex flex-wrap gap-2">
            {data!.offers[key]!.map((o) => (
              <a
                key={`${o.provider}-${o.deep_link}`}
                href={o.deep_link}
                target="_blank"
                rel="noopener noreferrer sponsored"
                onClick={() => track("provider_click", contentId)}
                className="group flex items-center gap-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] ring-1 ring-white/10 px-3 py-2 transition"
              >
                {o.provider_logo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={o.provider_logo} alt={o.provider} className="h-6 w-6 rounded object-contain" />
                ) : (
                  <span className="flex h-6 w-6 items-center justify-center rounded bg-white/10 text-[10px] font-bold">
                    {o.provider.slice(0, 2).toUpperCase()}
                  </span>
                )}
                <span className="text-sm font-medium">{o.provider}</span>
                {o.price != null && (
                  <span className="text-xs text-white/60">
                    {o.currency === "USD" ? "$" : ""}{o.price}
                  </span>
                )}
                <span className="text-white/40 group-hover:text-white/80 text-sm">↗</span>
              </a>
            ))}
          </div>
        </div>
      ))}
      <div className="text-[11px] text-white/40">
        Availability via JustWatch / TMDB. RO doesn&apos;t stream content — we link you to the services that do.
      </div>
    </div>
  );
}
