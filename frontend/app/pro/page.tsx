"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

const FEATURES = [
  { label: "AI chat", free: "50/day", pro: "500/day" },
  { label: "Agent tool calls", free: "✗", pro: "✓" },
  { label: "Watch parties", free: "2/week", pro: "Unlimited" },
  { label: "AI collections", free: "3 total", pro: "Unlimited + public sharing" },
  { label: "Spoiler-free rewrites", free: "✓", pro: "✓" },
  { label: "RO Wrapped", free: "✓ yearly", pro: "✓ + share card" },
  { label: "Blind Date", free: "✓ 1/week", pro: "Unlimited" },
  { label: "Mixer & co-viewer", free: "✓", pro: "✓ + save mixes" },
  { label: "Priority chat LLM", free: "smaller model", pro: "largest model" },
  { label: "Data export", free: "✓", pro: "✓ + scheduled weekly" },
];

export default function ProPage() {
  const router = useRouter();
  async function checkout() {
    const r = await api.post("/billing/checkout");
    if (r.data?.checkout_url) window.location.href = r.data.checkout_url;
  }
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <div className="text-center">
        <p className="text-xs uppercase tracking-widest text-brand">RO PLUS</p>
        <h1 className="mt-3 text-5xl md:text-6xl font-black">Unlock the whole engine.</h1>
        <p className="mt-4 text-white/60 max-w-xl mx-auto">
          The same Netflix-grade ranking, without quota. And a few things free users don&apos;t get.
        </p>
        <div className="mt-8 inline-flex items-baseline gap-1">
          <span className="text-5xl font-black">$6</span>
          <span className="text-white/60">/month</span>
        </div>
        <div className="mt-6">
          <Button onClick={checkout} className="text-base px-8 py-3">Upgrade</Button>
        </div>
      </div>

      <table className="mt-16 w-full text-sm">
        <thead>
          <tr className="text-white/50 text-xs uppercase">
            <th className="text-left py-2">Feature</th>
            <th className="py-2 w-32">Free</th>
            <th className="py-2 w-40 text-brand">Plus</th>
          </tr>
        </thead>
        <tbody>
          {FEATURES.map((f) => (
            <tr key={f.label} className="border-t border-white/10">
              <td className="py-3">{f.label}</td>
              <td className="py-3 text-white/70">{f.free}</td>
              <td className="py-3 text-brand font-semibold">{f.pro}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-12 rounded-md bg-white/5 p-5 text-xs text-white/50">
        Cancel anytime via /security. No ads on free tier, ever. Your data stays yours (GDPR export at /legal/privacy).
      </div>
    </div>
  );
}
