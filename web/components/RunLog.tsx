"use client";

import { useEffect, useRef, useState } from "react";

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

const STAGE_LABELS: Record<string, string> = {
  parsing: "Reading your file",
  cleaning: "Cleaning and encoding",
  training: "Training the stand-in model",
  measuring: "Measuring fairness",
  influence: "Computing feature influence",
  saving: "Saving results",
};

export default function RunLog({
  file,
  confirmations,
  onComplete,
  onError,
  onCancel,
}: RunLogProps) {
  const [frames, setFrames] = useState<Array<{ event: string; [key: string]: any }>>([]);
  const [aborted, setAborted] = useState(false);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
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
          throw new Error(body?.detail ?? `Request failed with ${res.status}`);
        }

        const reader = res.body?.getReader();
        if (!reader) {
          throw new Error("No response body");
        }
        readerRef.current = reader;

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
              callbacks.current.onError(frame.problem?.detail ?? "Analysis failed");
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

  const finished = frames.some((f) => f.event === "result");

  return (
    <section className="panel">
      <div className="panel__head">
        <h2>Running analysis</h2>
        <button
          onClick={handleCancel}
          disabled={finished || aborted}
          className="btn btn--destructive"
        >
          Cancel
        </button>
      </div>

      <div className="log" aria-live="polite">
        {frames.length === 0 && <p className="muted">Preparing…</p>}

        {frames.map((frame, i) => {
          if (frame.event === "stage") {
            const stageKey = frame.stage as string;
            return (
              <div key={i} className="log__row">
                <span
                  className={`log__dot${stageKey === "saving" ? " log__dot--done" : ""}`}
                  aria-hidden="true"
                />
                <div>
                  <p className="log__label">{frame.label}</p>
                  <p className="log__meta">
                    Stage {frame.index} of {frame.total}
                  </p>
                </div>
              </div>
            );
          }
          if (frame.event === "ping") {
            return (
              <div key={i} className="log__row log__row--ping">
                Waiting for stage to complete…
              </div>
            );
          }
          return null;
        })}
      </div>
    </section>
  );
}
