"use client";

import { useState } from "react";

interface ConfirmationCardProps {
  filename: string;
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

// The mapping panel is always editable; the old read/edit toggle added a mode
// for no reason (UI_UX 6.4).
export default function ConfirmationCard({
  filename,
  card,
  metadata,
  onConfirm,
  onSheetChange,
  onCancel,
}: ConfirmationCardProps) {
  const sheetNames = metadata.parse?.sheet_names ?? [];
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

  return (
    <div className="panel confirm">
      <div className="confirm__head">
        <h2>Confirm what this data means</h2>
      </div>

      <div className="confirm__grid">
        <div className="confirm__facts">
          <p className="confirm__file">{filename}</p>
          <p className="small muted">
            {metadata.rows.toLocaleString("en-US")} rows · {metadata.columns} columns
          </p>
          <p className="small muted">
            {card.groups.values.length} groups ·{" "}
            {card.factor_columns.length === 1
              ? "1 factor column"
              : `${card.factor_columns.length} factor columns`}
          </p>

          {sheetNames.length > 1 && (
            <div className="field" style={{ marginTop: 16 }}>
              <label htmlFor="confirm-sheet">Sheet</label>
              <select
                id="confirm-sheet"
                className="select"
                value={confirmations.sheet ?? sheetNames[0]}
                onChange={(e) => {
                  setConfirmations({ ...confirmations, sheet: e.target.value });
                  onSheetChange?.(e.target.value);
                }}
              >
                {sheetNames.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
              <p className="small faint">Choosing another sheet reads it again first.</p>
            </div>
          )}

          <details style={{ marginTop: 16 }}>
            <summary className="small">Show groups</summary>
            <ul className="small muted" style={{ margin: "8px 0 0", paddingLeft: 20 }}>
              {card.groups.values.map((group) => (
                <li key={group.label}>
                  {group.label} — {group.n.toLocaleString("en-US")} rows
                </li>
              ))}
            </ul>
          </details>
        </div>

        <div className="confirm__task">
          <div className="field">
            <label htmlFor="confirm-outcome">Outcome column</label>
            <select
              id="confirm-outcome"
              className="select"
              value={confirmations.outcome}
              onChange={(e) => setConfirmations({ ...confirmations, outcome: e.target.value })}
            >
              {metadata.column_names.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="confirm-positive">Positive value</label>
            <input
              id="confirm-positive"
              className="input"
              type="text"
              value={confirmations.positive}
              onChange={(e) => setConfirmations({ ...confirmations, positive: e.target.value })}
            />
            {confirmations.positive === card.outcome.positive_value && (
              <p className="small faint">
                {card.outcome.positive_count.toLocaleString("en-US")} of{" "}
                {card.outcome.total_rows.toLocaleString("en-US")} rows are positive
              </p>
            )}
          </div>

          <div className="field">
            <label htmlFor="confirm-group">Group column</label>
            <select
              id="confirm-group"
              className="select"
              value={confirmations.group}
              onChange={(e) => setConfirmations({ ...confirmations, group: e.target.value })}
            >
              {metadata.column_names.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          {card.age_banding.available && (
            <label className="small" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={confirmations.age_banding}
                onChange={(e) =>
                  setConfirmations({ ...confirmations, age_banding: e.target.checked })}
              />
              Group ages into 10-year bands
            </label>
          )}
        </div>
      </div>

      {card.warnings.length > 0 && (
        <div className="notice notice--warn confirm__block">
          <p style={{ fontWeight: 500 }}>Warnings</p>
          <ul>
            {card.warnings.map((warning, index) => (
              <li key={index}>{warning.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Sampling is an explicit choice above 50,000 rows (F1-AC3). */}
      {metadata.rows > 50000 && (
        <fieldset
          className="confirm__block"
          style={{ border: "1px solid var(--hairline)", borderRadius: 8, padding: 16 }}
        >
          <legend className="field-label" style={{ padding: "0 6px" }}>
            Rows to analyse
          </legend>
          <p className="small muted">
            This file has {metadata.rows.toLocaleString("en-US")} rows. Choose what to analyse:
          </p>
          <label className="small" style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <input type="radio" name="sampling" checked={samplingChoice === "sample"}
                   onChange={() => setSamplingChoice("sample")} />
            A seeded random sample of 50,000 rows (faster)
          </label>
          <label className="small" style={{ display: "flex", gap: 8, marginTop: 4 }}>
            <input type="radio" name="sampling" checked={samplingChoice === "all"}
                   onChange={() => setSamplingChoice("all")} />
            All {metadata.rows.toLocaleString("en-US")} rows
          </label>
        </fieldset>
      )}

      {blocked && (
        <p className="notice confirm__block">
          This demographic column has only one value, so a between-group comparison is not
          possible. Change the demographic column to continue.
        </p>
      )}

      <div className="confirm__actions">
        <button
          onClick={handleConfirm}
          disabled={blocked || needsSamplingChoice}
          className="btn btn--primary"
        >
          Run analysis
        </button>
        <button onClick={onCancel} className="btn btn--secondary">
          Cancel
        </button>
      </div>
    </div>
  );
}
