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

  return (
    <div style={{ border: "1px solid #E3E0D8", borderRadius: 4, padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, margin: 0 }}>Running analysis</h2>
        <button
          onClick={handleCancel}
          disabled={frames.some(f => f.event === "result") || aborted}
          style={{
            padding: "8px 16px", borderRadius: 2, border: "1px solid #8C2F2A",
            background: "#FAF9F6", color: "#8C2F2A", cursor: "pointer", fontSize: 14,
            opacity: frames.some(f => f.event === "result") || aborted ? 0.5 : 1,
          }}
        >
          Cancel
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {frames.map((frame, i) => {
          if (frame.event === "stage") {
            const stageKey = frame.stage as string;
            return (
              <div
                key={i}
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                  background: "#FAF9F6", borderRadius: 2, border: "1px solid #E3E0D8",
                }}
              >
                <div
                  style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: stageKey === "saving" ? "#1F5A3D" : "#17161A",
                  }}
                />
                <div style={{ flex: 1 }}>
                  <p style={{ margin: 0, fontSize: 15, color: "#17161A", fontWeight: 500 }}>
                    {frame.label}
                  </p>
                  <p style={{ margin: "2px 0 0", fontSize: 13, color: "#55525C" }}>
                    Stage {frame.index} of {frame.total}
                  </p>
                </div>
              </div>
            );
          }
          if (frame.event === "ping") {
            return (
              <div
                key={i}
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "8px 16px",
                  background: "#EEF1F6", borderRadius: 2, border: "1px solid #D6D3CC", fontSize: 13, color: "#3E4C63",
                }}
              >
                Waiting for stage to complete…
              </div>
            );
          }
          return null;
        })}

        {frames.length === 0 && (
          <div style={{ textAlign: "center", padding: 32, color: "#55525C" }}>
            Preparing…
          </div>
        )}
      </div>
    </div>
  );
}