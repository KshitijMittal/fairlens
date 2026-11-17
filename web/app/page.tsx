"use client";

import { useEffect, useState } from "react";
import Dropzone from "@/components/Dropzone";
import ConfirmationCard from "@/components/ConfirmationCard";
import RunLog from "@/components/RunLog";
import SampleRunButton from "@/components/SampleRunButton";

const SAMPLES = [
  {
    slug: "scholarship",
    name: "Scholarship awards",
    description:
      "Synthetic awards by region and age band. Fair by construction: all five checks pass.",
    expected: "Pass",
  },
  {
    slug: "loan_approvals",
    name: "Loan approvals",
    description:
      "Real historical lending decisions, subsampled from UCI German Credit. A large recorded disparity.",
    expected: "Fail",
  },
  {
    slug: "hiring_shortlist",
    name: "Hiring shortlist",
    description:
      "Synthetic shortlisting data with moderate disparity and a proxy column a drop-repair cannot fix.",
    expected: "Warn",
  },
];

type AppState = "idle" | "inspecting" | "confirming" | "running";

export default function Home() {
  const [state, setState] = useState<AppState>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [inspectResult, setInspectResult] = useState<{
    shape: { rows: number; columns: number };
    card: any;
    metadata: any;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmations, setConfirmations] = useState<any>(null);
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/v1/me", { credentials: "include", cache: "no-store" })
      .then((res) => setSignedIn(res.ok))
      .catch(() => setSignedIn(false));
  }, []);

  const handleFileSelect = async (selectedFile: File, sheet?: string) => {
    setError(null);
    setFile(selectedFile);
    setState("inspecting");

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (sheet) formData.append("sheet", sheet);

    try {
      const res = await fetch("/api/v1/analyses/inspect", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Inspect failed with ${res.status}`);
      }
      const data = await res.json();
      setInspectResult(data);
      setState("confirming");
    } catch (err: any) {
      setError(err.message ?? "Failed to inspect file");
      setState("idle");
      setFile(null);
    }
  };

  const handleConfirm = (confirmed: any) => {
    setConfirmations(confirmed);
    setState("running");
  };

  const handleCancel = () => {
    setState("idle");
    setFile(null);
    setInspectResult(null);
    setConfirmations(null);
    setError(null);
  };

  const handleRunComplete = (result: any) => {
    window.location.href = `/analysis/${result.id}`;
  };

  const handleRunError = (err: string) => {
    setError(err);
    setState("confirming");
  };

  return (
    <main className="page">
      <h1 className="display">FairLens</h1>
      <p className="lede muted" style={{ marginTop: 16, maxWidth: "42ch" }}>
        Check a dataset before a model learns from it.
      </p>

      <div style={{ marginTop: 96 }}>
        {state === "idle" && (
          <>
            {error && <p className="notice" style={{ marginBottom: 32 }}>{error}</p>}

            <section>
              <h2>Bundled samples</h2>
              <div style={{ marginTop: 32 }}>
                {SAMPLES.map((s, index) => (
                  <section
                    key={s.slug}
                    data-testid={`card-${s.slug}`}
                    className={`sample${index === SAMPLES.length - 1 ? " sample--last" : ""}`}
                  >
                    <div>
                      <h3>{s.name}</h3>
                      <p className="description">{s.description}</p>
                      <p className={`eyebrow expected expected--${s.expected.toLowerCase()}`}>
                        Expected: {s.expected}
                      </p>
                    </div>
                    <SampleRunButton slug={s.slug} label="Run the analysis" />
                  </section>
                ))}
              </div>
            </section>

            <section style={{ marginTop: 96 }}>
              <h2>Analyze your own file</h2>
              <p className="muted prose" style={{ marginTop: 16 }}>
                Upload a CSV or XLSX file (max 50 MB). You&apos;ll need to sign in to run the
                analysis.
              </p>
              <div style={{ marginTop: 32 }}>
                {signedIn === false ? (
                  <p className="muted">
                    <a href="/login">Sign in</a> or <a href="/signup">create an account</a> to
                    analyse your own file.
                  </p>
                ) : (
                  <Dropzone
                    onFileSelect={handleFileSelect}
                    acceptedTypes={[".csv", ".xlsx"]}
                    maxSizeMB={50}
                    disabled={signedIn === null}
                  />
                )}
              </div>
            </section>
          </>
        )}

        {state === "inspecting" && (
          <p className="muted" style={{ padding: "48px 0" }}>Inspecting file…</p>
        )}

        {state === "confirming" && inspectResult && (
          <ConfirmationCard
            card={inspectResult.card}
            metadata={inspectResult.metadata}
            onConfirm={handleConfirm}
            onSheetChange={(sheet) => file && handleFileSelect(file, sheet)}
            onCancel={handleCancel}
          />
        )}

        {state === "running" && file && confirmations && (
          <RunLog
            file={file}
            confirmations={confirmations}
            onComplete={handleRunComplete}
            onError={handleRunError}
            onCancel={handleCancel}
          />
        )}
      </div>
    </main>
  );
}
