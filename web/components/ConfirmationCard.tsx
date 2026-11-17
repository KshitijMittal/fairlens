"use client";

import { useState } from "react";

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
      <div className="panel">
        <div className="panel__head">
          <h2>Review &amp; change</h2>
          <button onClick={() => setEditing(false)} className="btn btn--secondary">
            Done
          </button>
        </div>

        <div className="form">
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
          </div>

          <div className="field">
            <label htmlFor="confirm-group">Demographic (group) column</label>
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
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={confirmations.age_banding}
                onChange={(e) =>
                  setConfirmations({ ...confirmations, age_banding: e.target.checked })}
              />
              <span style={{ fontSize: 15 }}>Group ages into 10-year bands</span>
            </label>
          )}

          <div className="form-row" style={{ marginTop: 8 }}>
            <button
              onClick={handleConfirm}
              disabled={blocked || needsSamplingChoice}
              className="btn btn--primary"
              style={{ flex: 1 }}
            >
              Run analysis
            </button>
            <button
              onClick={() => setEditing(false)}
              className="btn btn--secondary"
              style={{ flex: 1 }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel__head">
        <h2>Confirm what this data means</h2>
        <button onClick={handleChange} className="btn btn--text">
          Change
        </button>
      </div>

      <div className="tiles">
        <div className="tile">
          <p className="eyebrow">Outcome column</p>
          <p className="value">{confirmations.outcome}</p>
          <p className="muted" style={{ marginTop: 4, fontSize: 15, lineHeight: "22px" }}>
            Positive: <strong>{confirmations.positive}</strong>
            {confirmations.positive === card.outcome.positive_value
              ? ` (${card.outcome.positive_count} of ${card.outcome.total_rows})`
              : ""}
          </p>
        </div>

        <div className="tile">
          <p className="eyebrow">Demographic column</p>
          <p className="value">{confirmations.group}</p>
          <p className="muted" style={{ marginTop: 4, fontSize: 15, lineHeight: "22px" }}>
            {card.groups.values.length} groups
          </p>
          <details style={{ marginTop: 8 }}>
            <summary style={{ fontSize: 15 }}>Show groups</summary>
            <ul
              className="muted"
              style={{ margin: "8px 0 0", paddingLeft: 20, fontSize: 15, lineHeight: "22px" }}
            >
              {card.groups.values.map((g) => (
                <li key={g.label}>{g.label} — {g.n.toLocaleString()} rows</li>
              ))}
            </ul>
          </details>
        </div>

        <div className="tile">
          <p className="eyebrow">Age banding</p>
          <p className="value">
            {confirmations.age_banding
              ? "Applied (10-year bands)"
              : card.age_banding.available
                ? "Available, not applied"
                : "Not available"}
          </p>
        </div>

        <div className="tile">
          <p className="eyebrow">Factor columns</p>
          <p className="value">
            {card.factor_columns.length > 0 ? card.factor_columns.join(", ") : "None"}
          </p>
        </div>
      </div>

      {card.warnings.length > 0 && (
        <div className="notice notice--warn" style={{ marginTop: 24 }}>
          <p style={{ margin: "0 0 8px", fontWeight: 500 }}>Warnings</p>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {card.warnings.map((w, i) => (
              <li key={i}>{w.message}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="muted" style={{ marginTop: 24, fontSize: 15, lineHeight: "22px" }}>
        {metadata.rows.toLocaleString()} rows × {metadata.columns} columns
      </p>

      {/* A multi-sheet workbook names its sheets; the first is preselected (PRD F1). */}
      {sheetNames.length > 1 && (
        <div className="field" style={{ marginTop: 24 }}>
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
          <p className="faint" style={{ margin: "6px 0 0", fontSize: 13, lineHeight: "18px" }}>
            Choosing another sheet reads it again before the card is rebuilt.
          </p>
        </div>
      )}

      {/* Sampling is an explicit choice above 50,000 rows (F1-AC3). */}
      {metadata.rows > 50000 && (
        <fieldset
          style={{ marginTop: 24, padding: 16, border: "1px solid var(--hairline)", borderRadius: 2 }}
        >
          <legend className="field-label" style={{ padding: "0 6px" }}>
            Rows to analyse
          </legend>
          <p style={{ margin: "0 0 8px" }}>
            This file has {metadata.rows.toLocaleString()} rows. Choose what to analyse:
          </p>
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6,
            cursor: "pointer" }}>
            <input type="radio" name="sampling" checked={samplingChoice === "sample"}
                   onChange={() => setSamplingChoice("sample")} />
            <span style={{ fontSize: 15 }}>A seeded random sample of 50,000 rows (faster)</span>
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center", cursor: "pointer" }}>
            <input type="radio" name="sampling" checked={samplingChoice === "all"}
                   onChange={() => setSamplingChoice("all")} />
            <span style={{ fontSize: 15 }}>All {metadata.rows.toLocaleString()} rows</span>
          </label>
        </fieldset>
      )}

      {blocked && (
        <p className="notice" style={{ marginTop: 24 }}>
          This demographic column has only one value, so a between-group comparison is not
          possible. Change the demographic column above to continue.
        </p>
      )}

      <div className="form-row" style={{ marginTop: 24 }}>
        <button
          onClick={handleConfirm}
          disabled={blocked || needsSamplingChoice}
          className="btn btn--primary"
          style={{ flex: 1 }}
        >
          Run analysis
        </button>
        <button onClick={onCancel} className="btn btn--secondary" style={{ flex: 1 }}>
          Cancel
        </button>
      </div>
    </div>
  );
}
