"use client";

import { useState, useEffect } from "react";

interface ConfirmationCardProps {
  card: {
    outcome: {
      column: string;
      positive_value: string;
      positive_count: number;
      total_rows: number;
    };
    groups: {
      column: string;
      values: Array<{ label: string; n: number }>;
    };
    age_banding: {
      available: boolean;
      column: string | null;
      bands: Array<{ band: string; n: number; positives: number }>;
    };
    factor_columns: string[];
    warnings: Array<{ code: string; message: string }>;
  };
  metadata: {
    column_names: string[];
    dtypes: Record<string, string>;
    rows: number;
    columns: number;
    parse?: { sheet?: string; sheet_names?: string[] };
  };
  onConfirm: (confirmations: {
    outcome: string;
    positive: string;
    group: string;
    sheet?: string;
    age_banding: boolean;
    sampling?: { enabled: boolean; size: number };
  }) => void;
  onSheetChange?: (sheet: string) => void;
  onCancel: () => void;
}

export default function ConfirmationCard({
  card,
  metadata,
  onConfirm,
  onSheetChange,
  onCancel,
}: ConfirmationCardProps) {
  const sheetNames = metadata.parse?.sheet_names ?? [];
  const [editing, setEditing] = useState(false);
  const [samplingChoice, setSamplingChoice] = useState<"all" | "sample" | null>(
    metadata.rows <= 50000 ? "all" : null
  );
  const [confirmations, setConfirmations] = useState({
    outcome: card.outcome.column,
    positive: card.outcome.positive_value,
    group: card.groups.column,
    sheet: metadata.parse?.sheet,
    age_banding: false,
  });

  const blocked = card.warnings.some((w) => w.code === "single_value_demographic");
  const needsSamplingChoice = metadata.rows > 50000 && samplingChoice === null;

  const handleConfirm = () => {
    if (blocked || needsSamplingChoice) return;
    onConfirm({
      ...confirmations,
      sampling: samplingChoice === "sample"
        ? { enabled: true, size: 50000 }
        : { enabled: false, size: metadata.rows },
    });
  };

  const handleChange = () => {
    setEditing(true);
  };

  if (editing) {
    return (
      <div style={{ border: "1px solid #E3E0D8", borderRadius: 4, padding: 24, background: "#FAF9F6" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h2 style={{ fontSize: 22, margin: 0 }}>Review & change</h2>
          <button
            onClick={() => setEditing(false)}
            style={{ padding: "6px 12px", borderRadius: 2, border: "1px solid #D6D3CC", background: "#FAF9F6", color: "#17161A", cursor: "pointer" }}
          >
            Done
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Outcome column */}
          <div>
            <label style={{ display: "block", fontSize: 14, marginBottom: 6, color: "#17161A" }}>
              Outcome column
            </label>
            <select
              value={confirmations.outcome}
              onChange={(e) => setConfirmations({ ...confirmations, outcome: e.target.value })}
              style={{
                width: "100%", padding: "10px 12px", borderRadius: 2, border: "1px solid #D6D3CC",
                fontSize: 15, background: "white",
              }}
            >
              {metadata.column_names.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          {/* Positive value */}
          <div>
            <label style={{ display: "block", fontSize: 14, marginBottom: 6, color: "#17161A" }}>
              Positive value
            </label>
            <input
              type="text"
              value={confirmations.positive}
              onChange={(e) => setConfirmations({ ...confirmations, positive: e.target.value })}
              style={{
                width: "100%", padding: "10px 12px", borderRadius: 2, border: "1px solid #D6D3CC",
                fontSize: 15, background: "white",
              }}
            />
          </div>

          {/* Group column */}
          <div>
            <label style={{ display: "block", fontSize: 14, marginBottom: 6, color: "#17161A" }}>
              Demographic (group) column
            </label>
            <select
              value={confirmations.group}
              onChange={(e) => setConfirmations({ ...confirmations, group: e.target.value })}
              style={{
                width: "100%", padding: "10px 12px", borderRadius: 2, border: "1px solid #D6D3CC",
                fontSize: 15, background: "white",
              }}
            >
              {metadata.column_names.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          {/* Age banding */}
          {card.age_banding.available && (
            <div>
              <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={confirmations.age_banding}
                  onChange={(e) => setConfirmations({ ...confirmations, age_banding: e.target.checked })}
                />
                <span style={{ fontSize: 15, color: "#17161A" }}>
                  Group ages into 10-year bands
                </span>
              </label>
            </div>
          )}

          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <button
              onClick={handleConfirm}
              disabled={blocked || needsSamplingChoice}
              style={{
                flex: 1, padding: "12px", borderRadius: 2, border: "1px solid #17161A",
                background: "#17161A", color: "#FAF9F6", cursor: "pointer", fontSize: 16, fontWeight: 500,
                opacity: blocked || needsSamplingChoice ? 0.4 : 1,
              }}
            >
              Run analysis
            </button>
            <button
              onClick={() => setEditing(false)}
              style={{
                flex: 1, padding: "12px", borderRadius: 2, border: "1px solid #D6D3CC",
                background: "#FAF9F6", color: "#17161A", cursor: "pointer", fontSize: 16,
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  // View mode
  return (
    <div style={{ border: "1px solid #E3E0D8", borderRadius: 4, padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, margin: 0 }}>Confirm what this data means</h2>
        <button
          onClick={handleChange}
          style={{
            padding: "6px 12px", borderRadius: 2, border: "1px solid #D6D3CC",
            background: "#FAF9F6", color: "#17161A", cursor: "pointer", fontSize: 14,
          }}
        >
          Change
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        {/* Outcome */}
        <div style={{ background: "#FAF9F6", borderRadius: 2, padding: 16 }}>
          <p style={{ margin: "0 0 4px", fontSize: 13, color: "#8A8794", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Outcome column
          </p>
          <p style={{ margin: 0, fontSize: 17, fontWeight: 500, color: "#17161A" }}>
            {confirmations.outcome}
          </p>
          <p style={{ margin: "4px 0 0", fontSize: 14, color: "#55525C" }}>
            Positive: <strong>{confirmations.positive}</strong>
            {confirmations.positive === card.outcome.positive_value
              ? ` (${card.outcome.positive_count} of ${card.outcome.total_rows})`
              : ""}
          </p>
        </div>

        {/* Group */}
        <div style={{ background: "#FAF9F6", borderRadius: 2, padding: 16 }}>
          <p style={{ margin: "0 0 4px", fontSize: 13, color: "#8A8794", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Demographic column
          </p>
          <p style={{ margin: 0, fontSize: 17, fontWeight: 500, color: "#17161A" }}>
            {confirmations.group}
          </p>
          <p style={{ margin: "4px 0 0", fontSize: 14, color: "#55525C" }}>
            {card.groups.values.length} groups
          </p>
          <details style={{ marginTop: 8 }}>
            <summary style={{ cursor: "pointer", color: "#55525C", fontSize: 14 }}>Show groups</summary>
            <ul style={{ margin: "8px 0 0", paddingLeft: 20, fontSize: 14, color: "#55525C" }}>
              {card.groups.values.map((g) => (
                <li key={g.label}>{g.label} — {g.n.toLocaleString()} rows</li>
              ))}
            </ul>
          </details>
        </div>

        {/* Age banding */}
        <div style={{ background: "#FAF9F6", borderRadius: 2, padding: 16 }}>
          <p style={{ margin: "0 0 4px", fontSize: 13, color: "#8A8794", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Age banding
          </p>
          <p style={{ margin: 0, fontSize: 17, fontWeight: 500, color: "#17161A" }}>
            {confirmations.age_banding
              ? "Applied (10-year bands)"
              : card.age_banding.available
                ? "Available, not applied"
                : "Not available"}
          </p>
        </div>

        {/* Factors */}
        <div style={{ background: "#FAF9F6", borderRadius: 2, padding: 16 }}>
          <p style={{ margin: "0 0 4px", fontSize: 13, color: "#8A8794", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Factor columns
          </p>
          <p style={{ margin: 0, fontSize: 17, fontWeight: 500, color: "#17161A" }}>
            {card.factor_columns.length > 0 ? card.factor_columns.join(", ") : "None"}
          </p>
        </div>
      </div>

      {/* Warnings */}
      {card.warnings.length > 0 && (
        <div style={{ marginTop: 16, padding: 16, background: "#FBF3E4", border: "1px solid #E5D4A8", borderRadius: 2 }}>
          <p style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 500, color: "#8A5A12" }}>
            ⚠ Warnings
          </p>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, color: "#55525C" }}>
            {card.warnings.map((w, i) => (
              <li key={i}>{w.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Dataset info */}
      <div style={{ marginTop: 16, padding: 16, background: "#FAF9F6", borderRadius: 2, fontSize: 14, color: "#55525C" }}>
        <p style={{ margin: 0 }}>{metadata.rows.toLocaleString()} rows × {metadata.columns} columns</p>
      </div>

      {/* A multi-sheet workbook names its sheets; the first is preselected (PRD F1). */}
      {sheetNames.length > 1 && (
        <div style={{ marginTop: 16, padding: 16, border: "1px solid #E3E0D8", borderRadius: 2 }}>
          <label style={{ display: "block", fontSize: 14, fontWeight: 500, marginBottom: 6 }}>
            Sheet
          </label>
          <select
            value={confirmations.sheet ?? sheetNames[0]}
            onChange={(e) => {
              setConfirmations({ ...confirmations, sheet: e.target.value });
              onSheetChange?.(e.target.value);
            }}
            style={{ width: "100%", padding: "10px 12px", fontSize: 15, border: "1px solid #D6D3CC", borderRadius: 2 }}
          >
            {sheetNames.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: "#8A8794" }}>
            Choosing another sheet reads it again before the card is rebuilt.
          </p>
        </div>
      )}

      {/* Sampling is an explicit choice above 50,000 rows (F1-AC3). */}
      {metadata.rows > 50000 && (
        <div style={{ marginTop: 16, padding: 16, border: "1px solid #E3E0D8", borderRadius: 2 }}>
          <p style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 500 }}>
            This file has {metadata.rows.toLocaleString()} rows. Choose what to analyse:
          </p>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6, cursor: "pointer" }}>
            <input type="radio" name="sampling" checked={samplingChoice === "sample"}
                   onChange={() => setSamplingChoice("sample")} />
            <span style={{ fontSize: 14 }}>A seeded random sample of 50,000 rows (faster)</span>
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center", cursor: "pointer" }}>
            <input type="radio" name="sampling" checked={samplingChoice === "all"}
                   onChange={() => setSamplingChoice("all")} />
            <span style={{ fontSize: 14 }}>All {metadata.rows.toLocaleString()} rows</span>
          </label>
        </div>
      )}

      {blocked && (
        <p style={{ marginTop: 16, padding: 12, background: "#FBEDEB", border: "1px solid #F5C6C4", color: "#8C2F2A", fontSize: 14 }}>
          This demographic column has only one value, so a between-group comparison is not
          possible. Change the demographic column above to continue.
        </p>
      )}

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
        <button
          onClick={handleConfirm}
          disabled={blocked || needsSamplingChoice}
          style={{
            flex: 1, padding: "14px", borderRadius: 2, border: "1px solid #17161A",
            background: "#17161A", color: "#FAF9F6", cursor: "pointer", fontSize: 17, fontWeight: 500,
            opacity: blocked || needsSamplingChoice ? 0.4 : 1,
          }}
        >
          Run analysis
        </button>
        <button
          onClick={onCancel}
          style={{
            flex: 1, padding: "14px", borderRadius: 2, border: "1px solid #D6D3CC",
            background: "#FAF9F6", color: "#17161A", cursor: "pointer", fontSize: 17,
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}