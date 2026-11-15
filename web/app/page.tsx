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
    <>
      <main style={{ maxWidth: 880, margin: "0 auto", padding: "48px 24px", fontFamily: "system-ui" }}>
        <h1 style={{ fontSize: 40, lineHeight: 1.1, marginBottom: 8 }}>FairLens</h1>
        <p style={{ color: "#55525C", marginBottom: 40 }}>
          Check a dataset before a model learns from it.
        </p>

        {state === "idle" && (
          <>
            {error && (
              <div style={{ marginBottom: 24, padding: 16, background: "#FBEDEB", border: "1px solid #F5C6C4", borderRadius: 2, color: "#8C2F2A" }}>
                {error}
              </div>
            )}
            <section style={{ marginBottom: 48 }}>
              <h2 style={{ fontSize: 22, marginBottom: 16 }}>Bundled samples</h2>
              {SAMPLES.map((s) => (
                <section
                  key={s.slug}
                  data-testid={`card-${s.slug}`}
                  style={{ borderTop: "1px solid #E3E0D8", padding: "24px 0", display: "flex", gap: 24, alignItems: "center", justifyContent: "space-between" }}
                >
                  <div style={{ maxWidth: 560 }}>
                    <h3 style={{ fontSize: 22, margin: "0 0 6px" }}>{s.name}</h3>
                    <p style={{ color: "#55525C", margin: 0, fontSize: 15 }}>{s.description}</p>
                    <p style={{ color: "#8A8794", margin: "8px 0 0", fontSize: 13, letterSpacing: "0.06em", textTransform: "uppercase" }}>
                      Expected: {s.expected}
                    </p>
                  </div>
                  <SampleRunButton slug={s.slug} label="Run the analysis" />
                </section>
              ))}
            </section>

            <section>
              <h2 style={{ fontSize: 22, marginBottom: 16 }}>Analyze your own file</h2>
              <p style={{ color: "#55525C", marginBottom: 16 }}>
                Upload a CSV or XLSX file (max 50 MB). You'll need to sign in to run the analysis.
              </p>
              {signedIn === false ? (
                <p style={{ color: "#55525C", fontSize: 16 }}>
                  <a href="/login" style={{ color: "#17161A", textDecoration: "underline" }}>Sign in</a>
                  {" "}or{" "}
                  <a href="/signup" style={{ color: "#17161A", textDecoration: "underline" }}>create an account</a>
                  {" "}to analyse your own file.
                </p>
              ) : (
                <Dropzone
                  onFileSelect={handleFileSelect}
                  acceptedTypes={[".csv", ".xlsx"]}
                  maxSizeMB={50}
                  disabled={signedIn === null}
                />
              )}
            </section>
          </>
        )}

        {state === "inspecting" && (
          <div style={{ textAlign: "center", padding: 48 }}>
            <p style={{ color: "#55525C", fontSize: 17 }}>Inspecting file…</p>
          </div>
        )}

        {state === "confirming" && inspectResult && (
          <>
            <ConfirmationCard
              card={inspectResult.card}
              metadata={inspectResult.metadata}
              onConfirm={handleConfirm}
              onSheetChange={(sheet) => file && handleFileSelect(file, sheet)}
              onCancel={handleCancel}
            />
          </>
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
      </main>
    </>
  );
}