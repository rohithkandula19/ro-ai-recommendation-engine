"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";

export default function SecurityPage() {
  const [setup, setSetup] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [verifyMsg, setVerifyMsg] = useState<string | null>(null);
  const [confirm, setConfirm] = useState("");

  async function begin2fa() {
    const r = await api.post("/auth/2fa/setup");
    setSetup(r.data);
  }
  async function verify2fa() {
    try {
      await api.post("/auth/2fa/verify", { code });
      setVerifyMsg("✅ 2FA enabled");
    } catch (e: any) {
      setVerifyMsg(e?.response?.data?.detail ?? "invalid");
    }
  }
  async function deleteAccount() {
    if (!confirm) return;
    await api.post("/users/me/delete", { confirm });
    window.location.href = "/login";
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-10 space-y-10">
      <section>
        <h1 className="text-3xl font-extrabold">Security</h1>
      </section>

      <section className="rounded-lg bg-surface-elevated ring-1 ring-white/10 p-5">
        <h2 className="text-lg font-semibold">Two-factor authentication</h2>
        {!setup ? (
          <Button onClick={begin2fa} className="mt-3">Enable 2FA</Button>
        ) : (
          <div className="mt-3 space-y-3 text-sm">
            <p>Add this secret to your authenticator app:</p>
            <code className="block rounded bg-black/60 p-2 break-all">{setup.secret}</code>
            <p className="text-xs text-white/50">Or scan: <code>{setup.otpauth_uri}</code></p>
            <input value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} placeholder="6-digit code"
              className="w-full rounded bg-black/60 px-3 py-2 ring-1 ring-white/10" />
            <Button onClick={verify2fa}>Verify</Button>
            {verifyMsg && <p className="text-sm">{verifyMsg}</p>}
          </div>
        )}
      </section>

      <section className="rounded-lg bg-red-900/20 ring-1 ring-red-500/30 p-5">
        <h2 className="text-lg font-semibold text-red-300">Delete my account</h2>
        <p className="text-xs text-white/60 mt-2">Type your email to confirm. This cascades — everything is removed.</p>
        <input value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="your email"
          className="mt-3 w-full rounded bg-black/60 px-3 py-2 ring-1 ring-white/10" />
        <Button variant="secondary" onClick={deleteAccount} className="mt-3">Permanently delete</Button>
      </section>
    </div>
  );
}
