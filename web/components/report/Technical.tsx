import { type Analysis, type GroupRow, STATE, displayGroup, fixed, interval,
  thresholdText } from "./types";

const CELL = { fontSize: 15, lineHeight: "22px" } as const;

function Heading({ children }: { children: React.ReactNode }) {
  return (
    <h3 style={{ margin: "32px 0 12px", fontFamily: "var(--font-sans)", fontSize: 17,
      lineHeight: "27px", fontWeight: 600 }}>
      {children}
    </h3>
  );
}

function GroupTable({ caption, rows }: { caption: string; rows: GroupRow[] }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Group</th>
            <th scope="col" className="numeric">n</th>
            <th scope="col" className="numeric">Selection rate</th>
            <th scope="col" className="numeric">95% CI</th>
            <th scope="col" className="numeric">TPR</th>
            <th scope="col" className="numeric">FPR</th>
            <th scope="col" className="numeric">Accuracy</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                color: "var(--ink)", fontWeight: 400 }}>
                {displayGroup(row.label)}
              </th>
              <td className="numeric">{row.n}</td>
              <td className="numeric">{fixed(row.selection_rate)}</td>
              <td className="numeric">{interval(row.interval) || "—"}</td>
              <td className="numeric">{row.tpr === null ? "—" : fixed(row.tpr)}</td>
              <td className="numeric">{row.fpr === null ? "—" : fixed(row.fpr)}</td>
              <td className="numeric">{row.accuracy === null ? "—" : fixed(row.accuracy)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Technical({ result }: { result: Analysis }) {
  const card = result.model_card;
  const influence = result.influence;
  return (
    <details>
      <summary style={{ fontSize: 17 }}>Show the technical view</summary>
      <div style={{ marginTop: 24 }}>
        <p style={{ margin: 0, maxWidth: "66ch" }}>
          The model here is a stand-in, trained on this data to measure what the data teaches.
          It is not meant to be shipped; it exists so the checks describe a model trained on your
          data rather than a model in general.
        </p>

        <Heading>Metric table</Heading>
        <div style={{ overflowX: "auto" }}>
          <table>
            <caption>The five checks, their figures and the limits they are judged against</caption>
            <thead>
              <tr>
                <th scope="col">Check</th>
                <th scope="col">Metric</th>
                <th scope="col" className="numeric">Value</th>
                <th scope="col" className="numeric">95% CI</th>
                <th scope="col">Threshold</th>
                <th scope="col">State</th>
              </tr>
            </thead>
            <tbody data-testid="technical-metrics">
              {result.checks.map((check) => (
                <tr key={check.code}>
                  <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                    color: "var(--ink)", fontWeight: 400 }}>{check.code}</th>
                  <td style={CELL}>{check.name}</td>
                  <td className="numeric">{check.value === null ? "—" : fixed(check.value)}</td>
                  <td className="numeric">{interval(check.interval) || "—"}</td>
                  <td style={CELL}>{thresholdText(check)}</td>
                  <td style={{ ...CELL, color: `var(--${check.state})` }}>
                    {STATE[check.state].word}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <Heading>Per-group table</Heading>
        <GroupTable caption="Recorded decisions" rows={result.groups.historical} />
        <div style={{ height: 16 }} />
        <GroupTable caption="Model decisions (out-of-fold)" rows={result.groups.model} />
        <p style={{ ...CELL, color: "var(--ink-muted)", marginTop: 8 }}>
          True-positive rate, false-positive rate and accuracy are reported where the model
          predictions allow them.
        </p>

        <Heading>Model card</Heading>
        <dl style={{ margin: 0, display: "grid", gridTemplateColumns: "max-content 1fr",
          gap: "4px 24px", fontSize: 15, lineHeight: "22px" }}>
          <dt style={{ color: "var(--ink-muted)" }}>Algorithm</dt>
          <dd style={{ margin: 0 }}>{card.algorithm.replace(/_/g, " ")}</dd>
          <dt style={{ color: "var(--ink-muted)" }}>Hyperparameters</dt>
          <dd style={{ margin: 0 }}>
            {Object.entries(card.hyperparameters)
              .map(([key, value]) => `${key}=${value ?? "none"}`).join(", ")}
          </dd>
          <dt style={{ color: "var(--ink-muted)" }}>Folds</dt>
          <dd style={{ margin: 0 }}>{card.folds}</dd>
          <dt style={{ color: "var(--ink-muted)" }}>Out-of-fold accuracy</dt>
          <dd style={{ margin: 0 }}>{fixed(card.oof_accuracy)}</dd>
          <dt style={{ color: "var(--ink-muted)" }}>Positive label</dt>
          <dd style={{ margin: 0 }}>{card.positive_label}</dd>
          <dt style={{ color: "var(--ink-muted)" }}>Rows</dt>
          <dd style={{ margin: 0 }}>
            {result.dataset.rows.toLocaleString("en-US")} ·{" "}
            {result.confirmation.groups.values
              .map((row) => `${displayGroup(row.label)} ${row.n}`).join(" · ")}
          </dd>
          <dt style={{ color: "var(--ink-muted)" }}>Engine version</dt>
          <dd style={{ margin: 0 }}>{card.engine_version}</dd>
          <dt style={{ color: "var(--ink-muted)" }}>Date</dt>
          <dd style={{ margin: 0 }}>{new Date(result.created_at).toISOString().slice(0, 10)}</dd>
        </dl>

        <Heading>Encoding decisions</Heading>
        <div style={{ overflowX: "auto" }}>
          <table>
            <caption>How each column was encoded</caption>
            <thead>
              <tr>
                <th scope="col">Column</th>
                <th scope="col">Decision</th>
              </tr>
            </thead>
            <tbody>
              {result.encoding.categorical.map((row) => (
                <tr key={`cat-${row.column}`}>
                  <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                    color: "var(--ink)", fontWeight: 400 }}>{row.column}</th>
                  <td style={CELL}>{row.mapping}</td>
                </tr>
              ))}
              {result.encoding.numeric.map((row) => (
                <tr key={`num-${row.column}`}>
                  <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                    color: "var(--ink)", fontWeight: 400 }}>{row.column}</th>
                  <td style={CELL}>
                    numeric · median imputed {row.imputed_median ?? "—"}
                  </td>
                </tr>
              ))}
              {result.encoding.dropped.map((row) => (
                <tr key={`drop-${row.column}`}>
                  <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                    color: "var(--ink)", fontWeight: 400 }}>{row.column}</th>
                  <td style={CELL}>dropped · {row.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <Heading>Feature influence</Heading>
        {influence?.available && influence.features.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table>
              <caption>
                {influence.method}, top {influence.features.length}, on {influence.rows} rows
              </caption>
              <thead>
                <tr>
                  <th scope="col">Feature</th>
                  <th scope="col" className="numeric">Mean |SHAP|</th>
                </tr>
              </thead>
              <tbody>
                {influence.features.map((row) => (
                  <tr key={row.feature}>
                    <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                      color: "var(--ink)", fontWeight: 400 }}>{row.feature}</th>
                    <td className="numeric">{fixed(row.value, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ margin: 0, maxWidth: "66ch", color: "var(--ink-muted)" }}>
            {influence
              ? "Feature influence was unavailable for this run. The verdict and every other number are unaffected."
              : "This stored run has no feature-influence record."}
          </p>
        )}

        <Heading>Association with the group column</Heading>
        {result.proxies.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table>
              <caption>Columns associated with the group column, strongest first</caption>
              <thead>
                <tr>
                  <th scope="col">Column</th>
                  <th scope="col">Measure</th>
                  <th scope="col" className="numeric">Value</th>
                </tr>
              </thead>
              <tbody>
                {result.proxies.map((row) => (
                  <tr key={row.column}>
                    <th scope="row" style={{ ...CELL, textTransform: "none", letterSpacing: 0,
                      color: "var(--ink)", fontWeight: 400 }}>{row.column}</th>
                    <td style={CELL}>{row.measure.replace(/_/g, " ")}</td>
                    <td className="numeric">{fixed(row.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ margin: 0, maxWidth: "66ch", color: "var(--ink-muted)" }}>
            No column was associated with the group column above the reporting threshold.
          </p>
        )}

        <Heading>Sampling record</Heading>
        <p style={{ margin: 0, maxWidth: "66ch", color: "var(--ink-muted)" }}>
          {result.sampling
            ? `Random sample of ${String(result.sampling.sampled_rows)} rows from ` +
              `${String(result.sampling.original_rows)}, seed ${String(result.sampling.seed)}.`
            : "No sampling: the whole file was analysed."}
        </p>

        <a href={`/api/v1/analyses/${result.id}`} download={`fairlens-${result.id}.json`}
          style={{ display: "inline-block", marginTop: 32, fontSize: 17 }}>
          Download JSON
        </a>
      </div>
    </details>
  );
}
