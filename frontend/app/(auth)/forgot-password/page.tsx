"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post("/auth/password-reset/request", { email });
      setSent(true);
      setDevToken(r.data?.dev_token ?? null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-2xl font-bold">Reset your password</h1>
      {sent ? (
        <div className="mt-6 space-y-4 text-sm">
          <p className="text-white/70">If the email is registered, a reset link has been sent.</p>
          {devToken && (
            <div className="rounded-md bg-surface-elevated p-3 ring-1 ring-white/10">
              <p className="text-xs text-white/50 mb-1">DEV token (no email service configured):</p>
              <code className="text-xs break-all">{devToken}</code>
              <p className="mt-2 text-xs"><Link className="underline" href={`/reset-password?token=${encodeURIComponent(devToken)}`}>Use it →</Link></p>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input type="email" required placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md bg-black/60 px-3 py-2 ring-1 ring-white/10" />
          <Button type="submit" disabled={loading} className="w-full">{loading ? "…" : "Send reset link"}</Button>
        </form>
      )}
      <p className="mt-4 text-sm text-white/60">
        <Link href="/login" className="text-white underline">Back to sign in</Link>
      </p>
    </div>
  );
}
