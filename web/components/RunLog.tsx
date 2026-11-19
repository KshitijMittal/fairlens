"use client";

import { useEffect, useRef, useState } from "react";

import { apiError } from "@/lib/apiError";

interface RunLogProps {
  file: File;
  confirmations: {
    outcome: string;
    positive: string;
    group: string;
    age_banding: boolean;
    sampling?: { enabled: boolean; size: number };
  };
  onComplete: (result: any) => void;
  onError: (error: string) => void;
  onCancel: () => void;
}

// The backend's six stages, in order. Labels are printed unchanged (UI_UX 7.4).
const STAGES: [string, string][] = [
  ["parsing", "Reading your file"],
  ["cleaning", "Cleaning and encoding"],
  ["training", "Training the stand-in model"],
  ["measuring", "Measuring fairness"],
  ["influence", "Computing feature influence"],
  ["saving", "Saving results"],
];

export default function RunLog({
  file,
  confirmations,
  onComplete,
  onError,
  onCancel,
}: RunLogProps) {
  const [frames, setFrames] = useState<Array<{ event: string; [key: string]: any }>>([]);
  const [aborted, setAborted] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const abortedRef = useRef(false);
  const callbacks = useRef({ onComplete, onError });
  callbacks.current = { onComplete, onError };

  useEffect(() => {
    let mounted = true;
    abortControllerRef.current = new AbortController();

    async function runAnalysis() {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("confirmations", JSON.stringify(confirmations));

      try {
        const res = await fetch("/api/v1/analyses", {
          method: "POST",
          body: formData,
          credentials: "include",
          signal: abortControllerRef.current.signal,
        });

        if (!res.ok) {
          const body = await res.json().catch(() => null);
          throw new Error(apiError(body, res.status));
        }

        const reader = res.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          let newlineIndex;
          while ((newlineIndex = buffer.indexOf("\n")) >= 0) {
            const line = buffer.slice(0, newlineIndex).trim();
            buffer = buffer.slice(newlineIndex + 1);
            if (!line) continue;

            let frame: any;
            try {
              frame = JSON.parse(line);
            } catch {
              continue;
            }
            if (!mounted) return;
            setFrames((prev) => [...prev, frame]);

            if (frame.event === "result") {
              callbacks.current.onComplete(frame.payload);
              return;
            }
            if (frame.event === "error") {
              const detail = frame.problem?.detail;
              callbacks.current.onError(typeof detail === "string" ? detail : "Analysis failed");
              return;
            }
          }
        }

        if (mounted && !abortedRef.current) {
          callbacks.current.onError("Stream ended without a result.");
        }
      } catch (err: any) {
        if (err.name === "AbortError" || abortedRef.current) return;
        if (mounted) {
          callbacks.current.onError(err.message ?? "Analysis failed");
        }
      }
    }

    runAnalysis();

    return () => {
      mounted = false;
      abortControllerRef.current?.abort();
    };
  }, [file, confirmations]);

  const handleCancel = () => {
    abortedRef.current = true;
    setAborted(true);
    abortControllerRef.current?.abort();
    onCancel();
  };

  const finished = frames.some((frame) => frame.event === "result");
  // Stage frames arrive when a stage starts, so the last one is current.
  const current = frames.reduce(
    (highest, frame) => (frame.event === "stage" ? frame.index as number : highest), 0);

  return (
    <section className="stepper">
      <div className="stepper__head">
        <h2>Running analysis</h2>
        <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
          <p className="label">{current === 0 ? "Preparing" : `${current} of ${STAGES.length}`}</p>
          <button
            onClick={handleCancel}
            disabled={finished || aborted}
            className="btn btn--destructive"
          >
            Cancel
          </button>
        </div>
      </div>

      <div className="stepper__track" aria-hidden="true">
        <div
          className="stepper__fill"
          style={{ width: `${(Math.max(current - 1, 0) / STAGES.length) * 100}%` }}
        />
      </div>

      <ol className="stepper__list" aria-live="polite">
        {STAGES.map(([key, label], index) => {
          const step = index + 1;
          const status = step < current ? "done" : step === current ? "current" : "pending";
          return (
            <li
              key={key}
              className={`step-row step-row--${status}`}
              aria-current={status === "current" ? "step" : undefined}
            >
              <span className="step-row__glyph" aria-hidden="true">
                {status === "done" ? "✓" : status === "current" ? "●" : "○"}
              </span>
              {label}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
