"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import PasswordField, { passwordProblems } from "@/components/PasswordField";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitted(true);
    if (passwordProblems(password).length > 0) return;
    setBusy(true);
    try {
      const res = await fetch("/api/v1/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password, display_name: displayName || undefined }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(body?.detail ?? `Signup failed with ${res.status}`);
        return;
      }
      router.push("/");
      router.refresh();
    } catch {
      setError("The service could not be reached.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page page--narrow">
      <h1>Create an account</h1>
      <p className="muted" style={{ margin: "8px 0 32px" }}>
        Use email and password.
      </p>

      <form onSubmit={handleSubmit} className="form">
        <div className="field">
          <label htmlFor="signup-email">Email</label>
          <input
            id="signup-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="input"
          />
        </div>

        <div className="field">
          <label htmlFor="signup-name">Display name (optional)</label>
          <input
            id="signup-name"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={100}
            className="input"
          />
        </div>

        <PasswordField id="signup-password" value={password} onChange={setPassword} submitted={submitted} />

        {error && <p className="notice">{error}</p>}

        <button type="submit" disabled={busy} className="btn btn--primary btn--wide">
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="auth-foot">
        Already have an account? <Link href="/login">Sign in</Link>
      </p>
      <p className="auth-foot">
        <Link href="/reset">Reset password</Link>
      </p>
    </main>
  );
}
