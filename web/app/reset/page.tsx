"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const fieldStyle = {
  width: "100%", padding: "12px 14px", borderRadius: 2, border: "1px solid #D6D3CC",
  fontSize: 16, boxSizing: "border-box" as const,
};

export default function ResetPage() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState<"request" | "confirm" | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token"));
  }, []);

  async function post(path: string, body: object): Promise<boolean> {
    setError(null);
    setBusy(true);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        setError(payload?.detail ?? `Request failed with ${res.status}`);
        return false;
      }
      return true;
    } catch {
      setError("The service could not be reached.");
      return false;
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <main style={{ maxWidth: 440, margin: "64px auto", padding: "0 24px", fontFamily: "system-ui", textAlign: "center" }}>
        <h1 style={{ fontSize: 30, marginBottom: 16 }}>
          {done === "request" ? "Check your email" : "Password changed"}
        </h1>
        <p style={{ color: "#55525C", marginBottom: 32, fontSize: 17, lineHeight: 1.6 }}>
          {done === "request"
            ? "If an account with that email exists, a reset link has been sent. The link expires in 30 minutes."
            : "Your password has been reset and every other session has been signed out."}
        </p>
        <Link href="/login" style={{ color: "#17161A", textDecoration: "underline" }}>
          Back to sign in
        </Link>
      </main>
    );
  }

  const confirming = Boolean(token);

  return (
    <main style={{ maxWidth: 440, margin: "64px auto", padding: "0 24px", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 30, marginBottom: 8 }}>
        {confirming ? "Choose a new password" : "Reset your password"}
      </h1>
      <p style={{ color: "#55525C", marginBottom: 32 }}>
        {confirming
          ? "Enter a new password of at least 12 characters."
          : "Enter your email address and we'll send you a link to reset your password."}
      </p>

      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const ok = confirming
            ? await post("/api/v1/auth/reset/confirm", { token, password })
            : await post("/api/v1/auth/reset/request", { email });
          if (ok) setDone(confirming ? "confirm" : "request");
        }}
        style={{ display: "flex", flexDirection: "column", gap: 16 }}
      >
        <div>
          <label style={{ display: "block", fontSize: 14, marginBottom: 6, color: "#17161A" }}>
            {confirming ? "New password" : "Email"}
          </label>
          <input
            type={confirming ? "password" : "email"}
            value={confirming ? password : email}
            onChange={(e) => (confirming ? setPassword(e.target.value) : setEmail(e.target.value))}
            required
            minLength={confirming ? 12 : undefined}
            autoComplete={confirming ? "new-password" : "email"}
            style={fieldStyle}
          />
        </div>

        {error && <p style={{ color: "#8C2F2A", fontSize: 14 }}>{error}</p>}

        <button
          type="submit"
          disabled={busy}
          style={{
            padding: "12px", borderRadius: 2, border: "1px solid #17161A",
            background: "#17161A", color: "#FAF9F6", cursor: busy ? "wait" : "pointer",
            fontSize: 16, fontWeight: 500,
          }}
        >
          {busy ? "Working…" : confirming ? "Set new password" : "Send reset link"}
        </button>
      </form>

      <p style={{ marginTop: 24, color: "#55525C", fontSize: 15, textAlign: "center" }}>
        <Link href="/login" style={{ color: "#17161A", textDecoration: "underline" }}>Back to sign in</Link>
      </p>
    </main>
  );
}
