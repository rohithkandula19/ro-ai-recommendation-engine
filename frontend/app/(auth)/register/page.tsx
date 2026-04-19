"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

export default function RegisterPage() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, name);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-2xl font-bold">Create your account</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <input placeholder="Display name" value={name} required
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <input type="email" required placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <input type="password" required minLength={8} placeholder="Password (min 8)" value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">{loading ? "…" : "Create account"}</Button>
      </form>
      <p className="mt-4 text-sm text-white/60">
        Already have one? <Link href="/login" className="text-white underline">Sign in</Link>
      </p>
    </div>
  );
}
