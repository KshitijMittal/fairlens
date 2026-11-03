"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SampleRunButton({ slug, label }: { slug: string; label: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/dev/sample/${slug}`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(body?.detail ?? `Request failed with ${res.status}`);
        return;
      }
      const payload = await res.json();
      router.push(`/analysis/${payload.id}`);
    } catch {
      setError("The analysis service could not be reached.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button
        onClick={run}
        disabled={busy}
        data-testid={`run-${slug}`}
        style={{
          padding: "10px 18px", borderRadius: 2, border: "1px solid #17161A",
          background: "#17161A", color: "#FAF9F6", cursor: busy ? "wait" : "pointer",
          fontSize: 15,
        }}
      >
        {busy ? "Running…" : label}
      </button>
      {error && <p style={{ color: "#8C2F2A", fontSize: 14 }}>{error}</p>}
    </div>
  );
}
