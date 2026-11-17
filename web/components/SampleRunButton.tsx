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
        className="btn btn--primary"
      >
        {busy ? "Running…" : label}
      </button>
      {error && <p className="notice" style={{ marginTop: 12 }}>{error}</p>}
    </div>
  );
}
