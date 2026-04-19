"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

export default function LandingPage() {
  const { user, hydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (hydrated && user) router.replace("/browse");
  }, [hydrated, user, router]);

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-6">
      <h1 className="text-4xl md:text-6xl font-extrabold">Movies and series, picked for you.</h1>
      <p className="mt-4 max-w-xl text-white/70">Netflix-style recommendations powered by an ALS + two-tower + LTR pipeline over FAISS.</p>
      <div className="mt-8 flex gap-3">
        <Link href="/register"><Button>Get started</Button></Link>
        <Link href="/login"><Button variant="secondary">Sign in</Button></Link>
      </div>
    </div>
  );
}
