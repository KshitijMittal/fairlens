"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import PasswordField, { passwordProblems } from "@/components/PasswordField";
import StatusMark from "@/components/StatusMark";
import { apiError } from "@/lib/apiError";

export default function ResetPage() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [changed, setChanged] = useState(false);
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
        setError(apiError(payload, res.status));
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

  if (sentTo || changed) {
    return (
      <main className="auth">
        <div className="status" role="status" aria-live="polite">
          <StatusMark state="ok" />
          <h1>{changed ? "Password changed" : "Check your email"}</h1>
          <p className="auth__sub">
            {changed ? (
              "Your password has been reset and every other session has been signed out."
            ) : (
              <>
                If an account exists for <strong>{sentTo}</strong>, the link is on its way. It
                expires in 30 minutes. If it has not arrived within a few minutes, check the spam
                folder.
              </>
            )}
          </p>
        </div>
        {!changed && (
          <button
            type="button"
            className="btn btn--secondary btn--wide"
            onClick={() => {
              setSentTo(null);
              setError(null);
            }}
          >
            Change email
          </button>
        )}
        <p className="auth-foot" style={{ textAlign: "center" }}>
          <Link href="/login">Back to sign in</Link>
        </p>
      </main>
    );
  }

  const confirming = Boolean(token);

  return (
    <main className="auth">
      <h1>{confirming ? "Choose a new password" : "Reset your password"}</h1>
      <p className="auth__sub">
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
          if (!ok) return;
          if (confirming) setChanged(true);
          else setSentTo(email);
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

        {error && (
          <p className="notice notice--mark" role="alert">
            <StatusMark state="error" size={20} />
            <span>{error}</span>
          </p>
        )}

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
