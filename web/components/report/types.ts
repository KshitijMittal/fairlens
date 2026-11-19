export type VerdictState = "fail" | "warn" | "inconclusive" | "pass";

export interface Check {
  code: string;
  name: string;
  core: boolean;
  state: VerdictState;
  value: number | null;
  interval: [number, number] | null;
  threshold: Record<string, number | string>;
  method?: string;
  sentence: string;
  reason: string | null;
}

export interface GroupRow {
  label: string;
  n: number;
  positives: number;
  selection_rate: number;
  interval: [number, number] | null;
  tpr: number | null;
  fpr: number | null;
  accuracy: number | null;
}

export interface Analysis {
  id: string;
  created_at: string;
  engine_version: string;
  duration_ms: number;
  seed: number;
  dataset: { name: string; rows: number; columns: number; is_sample: boolean };
  confirmation: {
    outcome: { column: string; positive_value: string; positive_count: number };
    groups: { column: string; values: { label: string; n: number }[] };
    age_banding: { applied: boolean; bands: { band: string; n: number }[] | null };
    factor_columns: number;
  };
  verdict: VerdictState;
  deciding_checks: string[];
  lead: { state: VerdictState; headline: string; consequence: string };
  checks: Check[];
  groups: { historical: GroupRow[]; model: GroupRow[] };
  affected: { group: string; sentence: string }[];
  amplification: {
    sentence: string;
    detail: string;
    historical_gap: number;
    model_gap: number;
    difference: number;
  };
  model_card: {
    algorithm: string;
    hyperparameters: Record<string, number | string | null>;
    folds: number;
    oof_accuracy: number;
    oof_precision: number | null;
    oof_recall: number | null;
    positive_label: string;
    sensitive_as_feature: boolean;
    engine_version: string;
  };
  encoding: {
    categorical: { column: string; mapping: string }[];
    numeric: { column: string; imputed_median: number | null }[];
    dropped: { column: string; reason: string }[];
    grouped_rare: { column: string; reason: string }[];
  };
  influence?: {
    available: boolean;
    reason: string | null;
    method: string;
    rows: number;
    features: { feature: string; value: number }[];
  };
  proxies: { column: string; measure: string; value: number }[];
  sampling: Record<string, unknown> | null;
  thresholds: Record<string, Record<string, number>>;
  narrative: { kind: string; body: string; provider: string | null };
  privacy_line?: string;
  disclaimer?: string;
}

export const STATE: Record<VerdictState, { word: string; glyph: string }> = {
  fail: { word: "FAIL", glyph: "✕" },
  warn: { word: "WARN", glyph: "!" },
  inconclusive: { word: "INCONCLUSIVE", glyph: "?" },
  pass: { word: "PASS", glyph: "✓" },
};

export const DISPLAY_GROUPS: Record<string, string> = {
  female: "women",
  male: "men",
  group_a: "group a",
  group_b: "group b",
};

export function displayGroup(label: string): string {
  return DISPLAY_GROUPS[label] ?? label.replace(/_/g, " ").toLowerCase();
}

export function fixed(value: number, places = 3): string {
  return value.toFixed(places);
}

export function interval(ci: [number, number] | null): string {
  return ci ? `${fixed(ci[0])}–${fixed(ci[1])}` : "";
}

export function thresholdText(check: Check): string {
  const t = check.threshold;
  const n = (key: string) => Number(t[key]);
  if (check.code === "C5") {
    return `n ≥ ${n("min_group_rows")}` + "\n" + `CI half-width ≤ ${fixed(n("max_rate_half_width"), 2)}`;
  }
  if (check.code === "C3") {
    return `Warn ≥ ${fixed(n("warn_at"), 2)}` + "\n" + `Fail ≥ ${fixed(n("fail_at"), 2)}`;
  }
  if (t.direction === "below") {
    return `Pass ≤ ${fixed(n("pass_at"), 2)}` + "\n" + `Fail ≥ ${fixed(n("fail_at"), 2)}`;
  }
  return `Pass ≥ ${fixed(n("pass_at"), 2)}` + "\n" + `Warn ≥ ${fixed(n("warn_at"), 2)}`;
}
