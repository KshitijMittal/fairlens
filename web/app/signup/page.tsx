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
    <main style={{ maxWidth: 440, margin: "64px auto", padding: "0 24px", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 30, marginBottom: 8 }}>Create an account</h1>
      <p style={{ color: "#55525C", marginBottom: 32 }}>
        Use email and password.
      </p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <label style={{ display: "block", fontSize: 14, marginBottom: 6, color: "#17161A" }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            style={{
              width: "100%", padding: "12px 14px", borderRadius: 2, border: "1px solid #D6D3CC",
              fontSize: 16, boxSizing: "border-box",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: 14, marginBottom: 6, color: "#17161A" }}>
            Display name (optional)
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={100}
            style={{
              width: "100%", padding: "12px 14px", borderRadius: 2, border: "1px solid #D6D3CC",
              fontSize: 16, boxSizing: "border-box",
            }}
          />
        </div>

        <PasswordField id="signup-password" value={password} onChange={setPassword} submitted={submitted} />

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
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p style={{ marginTop: 24, color: "#55525C", fontSize: 15, textAlign: "center" }}>
        Already have an account? <Link href="/login" style={{ color: "#17161A", textDecoration: "underline" }}>Sign in</Link>
      </p>
      <p style={{ marginTop: 8, color: "#55525C", fontSize: 15, textAlign: "center" }}>
        <Link href="/reset" style={{ color: "#17161A", textDecoration: "underline" }}>Reset password</Link>
      </p>
    </main>
  );
}