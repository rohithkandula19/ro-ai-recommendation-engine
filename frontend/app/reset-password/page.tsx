"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

function Inner() {
  const sp = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const t = sp?.get("token") ?? "";
    if (t) setToken(t);
  }, [sp]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.post("/auth/password-reset/confirm", { token, new_password: password });
      setDone(true);
      setTimeout(() => router.replace("/login"), 1500);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Reset failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-2xl font-bold">Set a new password</h1>
      {done ? (
        <p className="mt-6 text-green-400">Password updated. Redirecting…</p>
      ) : (
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input required placeholder="Reset token" value={token}
            onChange={(e) => setToken(e.target.value)}
            className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
          <input type="password" required minLength={8} placeholder="New password (min 8)" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full">{loading ? "…" : "Update password"}</Button>
        </form>
      )}
      <p className="mt-4 text-sm text-white/60"><Link href="/login" className="text-white underline">Back to sign in</Link></p>
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<div className="p-8 text-white/60">Loading…</div>}><Inner /></Suspense>;
}
