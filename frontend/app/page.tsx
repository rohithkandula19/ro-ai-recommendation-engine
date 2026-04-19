"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

const FEATURES = [
  { icon: "🧬", title: "Taste DNA", desc: "6-axis profile learned from every watch. See yourself like a constellation." },
  { icon: "🎭", title: "Mood dial", desc: "Drag across chill ↔ tense and light ↔ thoughtful. Your picks morph in real time." },
  { icon: "⏱️", title: "Time-budget", desc: "Tell us you have 45 minutes. We find what fits, ranked by finish-rate." },
  { icon: "🤝", title: "Co-viewer", desc: "Blend two DNAs for the perfect household pick. The one you'll both tolerate." },
  { icon: "💬", title: "AI that remembers", desc: "Chat with RO — an agent that can rate, queue, and mark watched for you." },
  { icon: "🔍", title: "Semantic search", desc: "\"a slow thriller about memory\" → Memento. Vector search, not keywords." },
  { icon: "🎬", title: "Spoiler-free mode", desc: "LLM rewrites any description to tease without revealing." },
  { icon: "📊", title: "Why you'll like it", desc: "Every pick ships with a ranker explanation. No black-box recs." },
];

const STATS = [
  { n: "891", l: "Real titles" },
  { n: "394", l: "YouTube trailers" },
  { n: "6", l: "DNA dimensions" },
  { n: "210", l: "API endpoints" },
];

export default function LandingPage() {
  const { user, hydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && user) router.replace("/browse");
  }, [hydrated, user, router]);

  return (
    <div className="min-h-screen text-white">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-b from-[#14040a] via-black to-black" />
          <div className="absolute -top-40 -right-40 w-[700px] h-[700px] rounded-full blur-3xl"
               style={{ background: "radial-gradient(circle, rgba(229,9,20,0.35), transparent 65%)" }} />
        </div>
        <div className="mx-auto max-w-6xl px-6 pt-32 pb-24 text-center">
          <span className="inline-block rounded-full bg-white/5 px-4 py-1 text-xs tracking-wider text-white/70 ring-1 ring-white/10">
            NETFLIX-STYLE · AI-NATIVE · YOURS
          </span>
          <h1 className="mt-6 text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.05]">
            Streaming that <span className="text-brand">knows you</span>
            <br /> back.
          </h1>
          <p className="mt-6 max-w-2xl mx-auto text-lg text-white/70">
            RO is a recommendation engine built like a real product. ALS + FAISS + LightGBM LTR,
            a chat agent with memory, and 35+ features Netflix won&apos;t ship.
          </p>
          <div className="mt-8 flex justify-center gap-3 flex-wrap">
            <Link href="/register"><Button variant="primary" className="text-base px-6 py-3">Get started free</Button></Link>
            <Link href="/login"><Button variant="secondary" className="text-base px-6 py-3">Sign in</Button></Link>
          </div>
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
            {STATS.map((s) => (
              <div key={s.l}>
                <div className="text-3xl md:text-4xl font-extrabold text-brand">{s.n}</div>
                <div className="mt-1 text-xs uppercase tracking-wider text-white/50">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <h2 className="text-3xl md:text-5xl font-extrabold text-center">Built unlike anything else.</h2>
        <p className="mt-3 text-white/60 text-center max-w-xl mx-auto">The 9 features below exist because we don&apos;t have a content deal to protect.</p>
        <div className="mt-14 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f) => (
            <div key={f.title}
              className="rounded-xl bg-white/[0.03] ring-1 ring-white/10 p-6 hover:bg-white/[0.05] transition">
              <div className="text-3xl">{f.icon}</div>
              <div className="mt-4 text-lg font-bold">{f.title}</div>
              <div className="mt-2 text-sm text-white/60">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section className="mx-auto max-w-5xl px-6 py-20">
        <div className="rounded-2xl bg-gradient-to-br from-brand/10 to-transparent ring-1 ring-white/10 p-10 text-center">
          <h3 className="text-2xl md:text-3xl font-bold">Real engineering.</h3>
          <p className="mt-3 text-white/60 max-w-2xl mx-auto text-sm">
            Multi-stage ranking · partitioned interactions · Celery beat retrains · FAISS ANN · OpenRouter LLM with tool-calls.
            Distroless Dockerfiles, Terraform, k8s HPA. It ships.
          </p>
          <div className="mt-8 flex flex-wrap gap-2 justify-center">
            {["ALS", "FAISS", "LightGBM LTR", "MMR", "sentence-transformers", "WebSocket", "Kafka", "Celery", "Prometheus", "OpenTelemetry"].map((t) => (
              <span key={t} className="rounded-full bg-white/5 ring-1 ring-white/10 px-3 py-1 text-xs">{t}</span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-3xl px-6 py-24 text-center">
        <h3 className="text-3xl md:text-4xl font-extrabold">See your taste DNA in 60 seconds.</h3>
        <p className="mt-3 text-white/60">Sign up, rate a few titles, watch the radar reshape.</p>
        <div className="mt-8">
          <Link href="/register"><Button variant="primary" className="text-base px-8 py-3">Start free</Button></Link>
        </div>
      </section>
    </div>
  );
}
