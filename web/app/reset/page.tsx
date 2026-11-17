"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import PasswordField, { passwordProblems } from "@/components/PasswordField";

export default function ResetPage() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState<"request" | "confirm" | null>(null);
  const [submitted, setSubmitted] = useState(false);
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
      <main className="page page--narrow">
        <h1>{done === "request" ? "Check your email" : "Password changed"}</h1>
        <p className="muted" style={{ margin: "16px 0 32px" }}>
          {done === "request"
            ? "If an account with that email exists, a reset link has been sent. The link expires in 30 minutes. Check your spam folder if it has not arrived within a minute."
            : "Your password has been reset and every other session has been signed out."}
        </p>
        <Link href="/login" className="btn btn--text">
          Back to sign in
        </Link>
      </main>
    );
  }

  const confirming = Boolean(token);

  return (
    <main className="page page--narrow">
      <h1>{confirming ? "Choose a new password" : "Reset your password"}</h1>
      <p className="muted" style={{ margin: "8px 0 32px" }}>
        {confirming
          ? "Choose a new password. The rules are shown under the field."
          : "Enter your email address and we'll send you a link to reset your password."}
      </p>

      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (confirming) {
            setSubmitted(true);
            if (passwordProblems(password).length > 0) return;
          }
          const ok = confirming
            ? await post("/api/v1/auth/reset/confirm", { token, password })
            : await post("/api/v1/auth/reset/request", { email });
          if (ok) setDone(confirming ? "confirm" : "request");
        }}
        className="form"
      >
        {confirming ? (
          <PasswordField
            id="reset-password"
            label="New password"
            value={password}
            onChange={setPassword}
            submitted={submitted}
          />
        ) : (
          <div className="field">
            <label htmlFor="reset-email">Email</label>
            <input
              id="reset-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="input"
            />
          </div>
        )}

        {error && <p className="notice">{error}</p>}

        <button type="submit" disabled={busy} className="btn btn--primary btn--wide">
          {busy ? "Working…" : confirming ? "Set new password" : "Send reset link"}
        </button>
      </form>

      <p className="auth-foot">
        <Link href="/login">Back to sign in</Link>
      </p>
    </main>
  );
}
