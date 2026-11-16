import type { CSSProperties } from "react";

import { type Analysis, type Check, type GroupRow, STATE, displayGroup, fixed, interval,
  thresholdText } from "./types";
import Technical from "./Technical";

const MEASURE = "66ch";

function Section({ number, title, children }: {
  number: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section style={{ marginTop: 96 }}>
      <p style={{ margin: 0, fontSize: 13, lineHeight: "18px", letterSpacing: "0.06em",
        textTransform: "uppercase", fontWeight: 500, color: "var(--ink-faint)" }}>
        {number}
      </p>
      <h2 style={{ marginTop: 8, marginBottom: 32 }}>{title}</h2>
      {children}
    </section>
  );
}

function Verdict({ result }: { result: Analysis }) {
  const { state, headline, consequence } = result.lead;
  const stateWord = STATE[state];
  const unjudged = result.checks.filter((check) => check.state === "inconclusive");
  return (
    <section
      className="verdict-banner"
      data-testid="verdict-banner"
      data-verdict={state}
      style={{ background: `var(--${state}-tint)`, borderRadius: 2, padding: 32, marginTop: 24 }}
    >
      <p style={{ margin: 0, fontSize: 13, lineHeight: "18px", letterSpacing: "0.06em",
        textTransform: "uppercase", fontWeight: 500, color: `var(--${state})` }}>
        <span aria-hidden="true">{stateWord.glyph}</span> {stateWord.word}
      </p>
      <h1 data-testid="verdict-headline" style={{ margin: "12px 0 16px", color: "var(--ink)",
        maxWidth: "22ch" }}>
        {headline}
      </h1>
      <p style={{ margin: 0, maxWidth: MEASURE }}>{consequence}</p>
      {state === "inconclusive" && unjudged.length > 0 && (
        <p data-testid="unjudged-checks" style={{ margin: "16px 0 0", fontSize: 15,
          lineHeight: "22px", color: "var(--ink-muted)" }}>
          Could not judge: {unjudged.map((check) => `${check.code} ${check.name}`).join(", ")}.
        </p>
      )}
    </section>
  );
}

function Chart({ result }: { result: Analysis }) {
  const groups = [...result.groups.historical].sort(
    (a, b) => a.selection_rate - b.selection_rate);
  const model = new Map(result.groups.model.map((row) => [row.label, row]));
  const lowest = groups[0];
  const highest = groups[groups.length - 1];
  const least = lowest && highest && lowest.selection_rate < highest.selection_rate
    ? lowest.label
    : null;

  const labelWidth = 150;
  const plotX = 170;
  const plotWidth = 560;
  const block = 54;
  const top = 34;
  const height = top + groups.length * block + 8;
  const x = (rate: number) => plotX + rate * plotWidth;
  const labelled = (row: GroupRow) => `${displayGroup(row.label)} ${(row.selection_rate * 100).toFixed(1)}%`;

  const desc = `Recorded selection rate by group: ${groups.map(labelled).join(", ")}. ` +
    `Model: ${groups.map((row) => {
      const modelled = model.get(row.label);
      return modelled ? labelled(modelled) : displayGroup(row.label);
    }).join(", ")}.`;

  return (
    <figure style={{ margin: 0 }}>
      <div className="chart-scroll">
        <svg viewBox={`0 0 760 ${height}`} role="img" aria-labelledby="fl-chart-title"
          style={{ width: "100%", height: "auto", display: "block" }}>
        <title id="fl-chart-title">Selection rate by group, recorded and model</title>
        <desc>{desc}</desc>
        {[0, 25, 50, 75, 100].map((tick) => (
          <g key={tick}>
            <line x1={x(tick / 100)} x2={x(tick / 100)} y1={22} y2={height - 8}
              style={{ stroke: "var(--hairline)", strokeWidth: 1 }} />
            <text x={x(tick / 100)} y={14} textAnchor="middle"
              style={{ fill: "var(--ink-faint)", fontSize: 12 }}>
              {tick}%
            </text>
          </g>
        ))}
        {groups.map((row, index) => {
          const y = top + index * block;
          const modelled = model.get(row.label);
          const lines = wrap(displayGroup(row.label), 16);
          return (
            <g key={row.label}>
              {lines.map((line, lineIndex) => (
                <text key={line} x={0} y={y + 14 + lineIndex * 19}
                  style={{ fill: "var(--ink)", fontSize: 15 }}>
                  {line}
                </text>
              ))}
              {row.label === least && result.verdict !== "pass" && (
                <text x={0} y={y + 14 + lines.length * 19}
                  style={{ fill: "var(--ink-muted)", fontSize: 12, letterSpacing: "0.06em",
                    textTransform: "uppercase" }}>
                  least selected
                </text>
              )}
              <Bar rate={row.selection_rate} y={y} kind="recorded" delay={index} />
              <Interval row={row} y={y} x={x} kind="recorded" />
              {modelled && (
                <>
                  <Bar rate={modelled.selection_rate} y={y + 20} kind="model" delay={index} />
                  <Interval row={modelled} y={y + 20} x={x} kind="model" />
                </>
              )}
            </g>
          );
        })}
      </svg>
      </div>
      <p style={{ margin: "16px 0 0", fontSize: 15, lineHeight: "22px", color: "var(--ink-muted)" }}>
        Filled bar: the decisions recorded in your data. Outlined bar: the model. The line through
        each bar is its 95% interval. Axis starts at zero.
      </p>
      <details style={{ marginTop: 16 }}>
        <summary style={{ fontSize: 17 }}>Data table</summary>
        <div style={{ overflowX: "auto", marginTop: 16 }}>
          <table>
            <caption>Selection rate by group, recorded and model</caption>
            <thead>
              <tr>
                <th scope="col">Group</th>
                <th scope="col" className="numeric">Recorded rows</th>
                <th scope="col" className="numeric">Recorded rate</th>
                <th scope="col" className="numeric">Recorded 95% CI</th>
                <th scope="col" className="numeric">Model rate</th>
              </tr>
            </thead>
            <tbody>
              {groups.map((row) => {
                const modelled = model.get(row.label);
                return (
                  <tr key={row.label}>
                    <th scope="row" style={{ textTransform: "none", letterSpacing: 0,
                      fontSize: 15, color: "var(--ink)", fontWeight: 400 }}>
                      {displayGroup(row.label)}
                    </th>
                    <td className="numeric">{row.n}</td>
                    <td className="numeric">{fixed(row.selection_rate)}</td>
                    <td className="numeric">{interval(row.interval)}</td>
                    <td className="numeric">{modelled ? fixed(modelled.selection_rate) : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

function Bar({ rate, y, kind, delay }: { rate: number; y: number; kind: "recorded" | "model";
  delay: number }) {
  const width = Math.max(rate * 560, 0);
  return (
    <rect className="chart-bar" x={170} y={y} width={width} height={14}
      style={{
        fill: kind === "recorded" ? "var(--ink)" : "none",
        fillOpacity: kind === "recorded" ? 0.85 : 1,
        stroke: kind === "model" ? "var(--accent)" : "none",
        strokeWidth: kind === "model" ? 2 : 0,
        animationDelay: `${delay * 60}ms`,
      }} />
  );
}

function Interval({ row, y, x, kind }: { row: GroupRow; y: number; x: (rate: number) => number;
  kind: "recorded" | "model" }) {
  if (!row.interval) return null;
  const [low, high] = row.interval;
  const centre = y + 7;
  return (
    <g style={{ stroke: "var(--ink-muted)", strokeWidth: 2 }}>
      <line x1={x(low)} x2={x(high)} y1={centre} y2={centre}
        strokeDasharray={kind === "model" ? "3 3" : undefined} />
      <line x1={x(low)} x2={x(low)} y1={centre - 5} y2={centre + 5} />
      <line x1={x(high)} x2={x(high)} y1={centre - 5} y2={centre + 5} />
    </g>
  );
}

function wrap(text: string, width: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  for (const word of words) {
    const last = lines[lines.length - 1];
    if (last && `${last} ${word}`.length <= width) {
      lines[lines.length - 1] = `${last} ${word}`;
    } else {
      lines.push(word);
    }
  }
  return lines;
}

function Checks({ result }: { result: Analysis }) {
  const counts = result.confirmation.groups.values;
  return (
    <div>
      {result.checks.map((check, index) => (
        <CheckRow key={check.code} check={check} index={index} counts={counts} />
      ))}
    </div>
  );
}

function CheckRow({ check, index, counts }: {
  check: Check;
  index: number;
  counts: { label: string; n: number }[];
}) {
  const stateWord = STATE[check.state];
  return (
    <article
      data-testid={`check-${check.code}`}
      data-state={check.state}
      className="check-row"
      style={{ "--index": index, borderTop: "1px solid var(--hairline)", padding: "24px 0" } as CSSProperties}
    >
      <div className="check-row__body">
        <div>
          <p style={{ margin: 0, fontSize: 13, lineHeight: "18px", letterSpacing: "0.06em",
            textTransform: "uppercase", fontWeight: 500, color: "var(--ink-faint)" }}>
            {check.code}{check.core ? " · core" : ""}
          </p>
          <p style={{ margin: "4px 0 8px", fontWeight: 500 }}>{check.name}</p>
          <p style={{ margin: 0, color: "var(--ink-muted)", maxWidth: "52ch" }}>{check.sentence}</p>
        </div>
        <div className="check-row__figure">
          <p style={{ margin: 0, fontSize: 13, lineHeight: "18px", letterSpacing: "0.06em",
            textTransform: "uppercase", fontWeight: 500, color: `var(--${check.state})` }}>
            <span aria-hidden="true">{stateWord.glyph}</span> {stateWord.word}
          </p>
          {check.value !== null && (
            <p data-testid={`figure-${check.code}`} className="serif"
              style={{ margin: "8px 0 0", fontSize: 22, lineHeight: "26px" }}>
              {fixed(check.value)}
            </p>
          )}
          {check.interval && (
            <p style={{ margin: "4px 0 0", fontSize: 15, lineHeight: "22px",
              color: "var(--ink-muted)" }}>
              95% CI {interval(check.interval)}
            </p>
          )}
          <p data-testid={`threshold-${check.code}`} style={{ margin: "8px 0 0", fontSize: 15,
            lineHeight: "22px", color: "var(--ink-faint)" }}>
            {thresholdText(check)}
          </p>
        </div>
      </div>
      <details open={check.state === "inconclusive"} style={{ marginTop: 16 }}>
        <summary style={{ fontSize: 15 }}>Method and group counts</summary>
        <div style={{ marginTop: 8, fontSize: 15, lineHeight: "22px", color: "var(--ink-muted)",
          maxWidth: "66ch" }}>
          <p style={{ margin: 0 }}>{check.method ?? "No method recorded for this run."}</p>
          <p style={{ margin: "4px 0 0" }}>
            {counts.map((row) => `${displayGroup(row.label)} ${row.n} rows`).join(" · ")}
          </p>
        </div>
      </details>
    </article>
  );
}

function Affected({ result }: { result: Analysis }) {
  return (
    <>
      {result.affected.length > 0 && (
        <div style={{ marginTop: 32 }}>
          {result.affected.map((row) => (
            <p key={row.group} style={{ margin: "0 0 8px", maxWidth: MEASURE }}>
              {row.sentence}
            </p>
          ))}
        </div>
      )}
      <div style={{ marginTop: 32, paddingTop: 24, borderTop: "1px solid var(--hairline)" }}>
        <p className="serif" style={{ margin: 0, fontSize: 21, lineHeight: "32px",
          maxWidth: MEASURE }}>
          {result.amplification.sentence}
        </p>
        <p style={{ margin: "8px 0 0", maxWidth: MEASURE }}>{result.amplification.detail}</p>
      </div>
    </>
  );
}

export default function Report({ result }: { result: Analysis }) {
  return (
    <main style={{ maxWidth: "78rem", margin: "0 auto", padding: "0 clamp(24px, 5vw, 64px) 96px" }}>
      <p style={{ margin: "32px 0 0", fontSize: 15, lineHeight: "22px", color: "var(--ink-muted)" }}>
        {result.dataset.name} · {result.dataset.rows.toLocaleString("en-US")} rows ·{" "}
        {new Date(result.created_at).toISOString().slice(0, 10)}
      </p>

      <p style={{ margin: 0, fontSize: 13, lineHeight: "18px", letterSpacing: "0.06em",
        textTransform: "uppercase", fontWeight: 500, color: "var(--ink-faint)" }}>
        01
      </p>
      <h2 style={{ marginTop: 8, marginBottom: 32 }}>The verdict</h2>
      <Verdict result={result} />
      <p style={{ margin: "16px 0 0", fontSize: 15, lineHeight: "22px", color: "var(--ink-muted)",
        maxWidth: MEASURE }}>
        {result.privacy_line}
      </p>

      <Section number="02" title="Who is affected">
        <Chart result={result} />
        <Affected result={result} />
      </Section>

      <Section number="03" title="What the model does">
        <Checks result={result} />
        <p className="narrative serif" style={{ margin: "48px 0 0", fontSize: 21,
          lineHeight: "32px", maxWidth: MEASURE }}>
          {result.narrative.body}
        </p>
      </Section>

      <Section number="04" title="The method">
        <Technical result={result} />
      </Section>

      <footer style={{ marginTop: 96, paddingTop: 24, borderTop: "1px solid var(--hairline)",
        fontSize: 15, lineHeight: "22px", color: "var(--ink-muted)" }}>
        <p style={{ margin: 0, maxWidth: MEASURE }}>{result.privacy_line}</p>
        <p style={{ margin: "8px 0 0", maxWidth: MEASURE }}>{result.disclaimer}</p>
        <p style={{ margin: "16px 0 0", color: "var(--ink-faint)" }}>
          Template-generated narrative · engine {result.engine_version} · {result.duration_ms} ms
        </p>
      </footer>
    </main>
  );
}
