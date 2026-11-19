"use client";

import { useState } from "react";

import ConfirmationCard from "@/components/ConfirmationCard";
import Dropzone from "@/components/Dropzone";
import RunLog from "@/components/RunLog";
import SampleRunButton from "@/components/SampleRunButton";
import { useAuth } from "@/components/AuthProvider";
import { apiError } from "@/lib/apiError";
import { STATE } from "@/components/report/types";
import type { VerdictState } from "@/components/report/types";

const SAMPLES: {
  slug: string;
  name: string;
  shape: string;
  description: string;
  expected: VerdictState;
}[] = [
  {
    slug: "scholarship",
    name: "Scholarship awards",
    shape: "1,440 rows · 6 columns",
    description:
      "Synthetic awards by region and age band. Fair by construction: all five checks pass.",
    expected: "pass",
  },
  {
    slug: "loan_approvals",
    name: "Loan approvals",
    shape: "908 rows · 10 columns",
    description:
      "Real historical lending decisions, subsampled from UCI German Credit. A large recorded disparity.",
    expected: "fail",
  },
  {
    slug: "hiring_shortlist",
    name: "Hiring shortlist",
    shape: "1,400 rows · 7 columns",
    description:
      "Synthetic shortlisting data with moderate disparity and a proxy column a drop-repair cannot fix.",
    expected: "warn",
  },
];

type AppState = "idle" | "inspecting" | "confirming" | "running";

export default function Home() {
  const { user, loading, openAuth } = useAuth();
  const [state, setState] = useState<AppState>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [inspectResult, setInspectResult] = useState<{
    shape: { rows: number; columns: number };
    card: any;
    metadata: any;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmations, setConfirmations] = useState<any>(null);

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
        throw new Error(apiError(body, res.status));
      }
      setInspectResult(await res.json());
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

  // A selected file replaces the landing content in place (UI_UX 5.5).
  if (state !== "idle") {
    return (
      <main className="shell" style={{ maxWidth: 880, paddingTop: 48, paddingBottom: 96 }}>
        {error && (
          <p className="notice" style={{ marginBottom: 24 }}>
            {error}
          </p>
        )}
        {state === "inspecting" && (
          <div className="panel" style={{ maxWidth: 720 }} aria-live="polite">
            <p className="label">Reading your file</p>
            <p className="muted" style={{ marginTop: 8 }}>
              Inspecting {file?.name}…
            </p>
          </div>
        )}
        {state === "confirming" && inspectResult && (
          <ConfirmationCard
            filename={file?.name ?? ""}
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
      </main>
    );
  }

  return (
    <main>
      <section className="hero">
        <div className="shell hero__grid">
          <div>
            <p className="label">Data fairness, before training</p>
            <h1 className="display" style={{ marginTop: 12 }}>
              Know what your data teaches before a model learns it.
            </h1>
            <p className="hero__body">
              FairLens reads a CSV or XLSX, trains a throwaway model on it, and reports where it
              would pass on unequal treatment — five checks, one verdict, every figure explained.
            </p>
          </div>

          {/* The tool is the hero's second column: one primary action, in place,
              with no button that scrolls to a second copy of it (UI_UX 5.2). */}
          <div id="analyse" className="hero__panel">
            {loading ? (
              <p className="muted">Checking your session…</p>
            ) : user ? (
              <Dropzone onFileSelect={handleFileSelect} acceptedTypes={[".csv", ".xlsx"]} maxSizeMB={50} />
            ) : (
              // Same surface signed out: the dropzone is the product, and it
              // opens sign-in in place rather than pointing at another button.
              <Dropzone
                locked
                onFileSelect={handleFileSelect}
                onLockedClick={() => openAuth("signin")}
                hint="Click to sign in — samples need no account"
              />
            )}
            <p className="small upload__constraints">
              CSV or XLSX · up to 50 MB · read in memory, not kept
            </p>
            {error && (
              <p className="notice" style={{ marginTop: 12 }}>
                {error}
              </p>
            )}
            <p className="small hero__note">
              No file to hand? <a href="#samples">Run a sample</a>
            </p>
          </div>
        </div>
      </section>

      <section id="samples" className="section shell section-anchor">
        <div className="section__head">
          <h2>Three datasets, three known answers</h2>
        </div>
        <p className="section__body">Run one to see the full report without uploading anything.</p>

        <ul className="cards">
          {SAMPLES.map((sample) => {
            const word = STATE[sample.expected];
            return (
              <li key={sample.slug} className="card" data-testid={`card-${sample.slug}`}>
                <h3>{sample.name}</h3>
                <p className="card__meta">{sample.shape}</p>
                <p className="card__desc">{sample.description}</p>
                <p className="card__expected small">
                  <span className={`chip chip--${sample.expected}`}>
                    <span aria-hidden="true">{word.glyph}</span> {word.word}
                  </span>
                  Expected
                </p>
                <div className="card__foot">
                  <SampleRunButton slug={sample.slug} label="Run the analysis" />
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <footer className="footer">
        <div className="shell footer__row small">
          <p>
            {/* UI_UX 7.5-7.6: the same promise the server puts on every report, in
                the present tense, because no file has been processed on this page. */}
            Your file is read in memory and not kept. What is saved is the numbers in the
            report — and deleting your account removes them.
          </p>
          <p>
            <a href="https://github.com/KshitijMittal/fairlens">GitHub</a>
          </p>
        </div>
        <div className="shell" style={{ marginTop: 8 }}>
          <p className="small">
            These limits are our defaults, based on the common 80% rule. They are not a legal
            determination.
          </p>
        </div>
      </footer>
    </main>
  );
}
