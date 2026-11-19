import type { CSSProperties } from "react";

import { type Analysis, type Check, type GroupRow, STATE, displayGroup, fixed, interval,
  thresholdText } from "./types";
import Technical from "./Technical";

const SECTIONS = [
  { id: "verdict", title: "The verdict" },
  { id: "checks", title: "The checks" },
  { id: "affected", title: "Who is affected" },
  { id: "meaning", title: "What this means" },
  { id: "method", title: "The method" },
];

const pad = (index: number) => String(index + 1).padStart(2, "0");

function Section({ id, index, title, children }: {
  id: string;
  index: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="section-anchor" style={{ "--index": index } as CSSProperties}>
      <p className="label">{pad(index)}</p>
      <h2 style={{ marginTop: 8, marginBottom: 16 }}>{title}</h2>
      {children}
    </section>
  );
}

function Kpi({ result }: { result: Analysis }) {
  const ratios = result.checks
    .filter((check) => (check.code === "C1" || check.code === "C2") && check.value !== null)
    .sort((a, b) => (a.value as number) - (b.value as number));
  const lowest = ratios[0];
  const figures = [
    lowest && { value: fixed(lowest.value as number), label: `Lowest ratio · ${lowest.code}` },
    {
      value: `${Math.round(result.amplification.model_gap * 100)} pts`,
      label: "Model gap",
    },
    { value: result.dataset.rows.toLocaleString("en-US"), label: "Rows analysed" },
  ].filter(Boolean) as { value: string; label: string }[];

  return (
    <div className="kpi">
      {figures.map((figure) => (
        <div key={figure.label}>
          <p className="kpi__value">{figure.value}</p>
          <p className="kpi__label" style={{ color: `var(--${result.verdict})` }}>
            {figure.label}
          </p>
        </div>
      ))}
    </div>
  );
}

function Verdict({ result }: { result: Analysis }) {
  const { state, headline, consequence } = result.lead;
  const stateWord = STATE[state];
  const unjudged = result.checks.filter((check) => check.state === "inconclusive");
  return (
    <section
      className="verdict"
      data-testid="verdict-banner"
      data-verdict={state}
      style={{ background: `var(--${state}-tint)` }}
    >
      <p className="verdict__head">
        <span className={`chip chip--${state}`}>
          <span aria-hidden="true">{stateWord.glyph}</span> {stateWord.word}
        </span>
      </p>
      <h1 className="display" data-testid="verdict-headline">
        {headline}
      </h1>
      <p className="verdict__consequence">{consequence}</p>
      {state === "inconclusive" && unjudged.length > 0 && (
        <p className="verdict__unjudged small" data-testid="unjudged-checks">
          Could not judge: {unjudged.map((check) => `${check.code} ${check.name}`).join(", ")}.
        </p>
      )}
      <Kpi result={result} />
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
                  style={{ fill: "var(--ink)", fontSize: 13 }}>
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
      <figcaption className="chart-note">
        Filled bar: the decisions recorded in your data. Outlined bar: the model. The line through
        each bar is its 95% interval. Axis starts at zero.
      </figcaption>
      <details style={{ marginTop: 16 }}>
        <summary>Data table</summary>
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
                    <th scope="row">{displayGroup(row.label)}</th>
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
        stroke: kind === "model" ? "var(--ink-faint)" : "none",
        strokeWidth: kind === "model" ? 1.5 : 0,
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
    <g style={{ stroke: "var(--ink-muted)", strokeWidth: 1 }}>
      <line x1={x(low)} x2={x(high)} y1={centre} y2={centre}
        strokeDasharray={kind === "model" ? "3 3" : undefined} />
      <line x1={x(low)} x2={x(low)} y1={centre - 6} y2={centre + 6} />
      <line x1={x(high)} x2={x(high)} y1={centre - 6} y2={centre + 6} />
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
    <div className="checks">
      {result.checks.map((check) => (
        <CheckRow key={check.code} check={check} counts={counts} />
      ))}
    </div>
  );
}

function CheckRow({ check, counts }: {
  check: Check;
  counts: { label: string; n: number }[];
}) {
  const stateWord = STATE[check.state];
  return (
    <article className="check" data-testid={`check-${check.code}`} data-state={check.state}>
      {/* Inconclusive rows never collapse (PRD F4-AC3). */}
      <details open={check.state === "inconclusive"}>
        <summary>
          <span className="check__code">
            {check.code}
            {check.core && <span className="check__core">core</span>}
          </span>
          <span>
            <span className="check__name">{check.name}</span>
            <span className="check__meaning">{check.sentence}</span>
          </span>
          <span>
            {check.value !== null && (
              <span className="check__figure" data-testid={`figure-${check.code}`}>
                {fixed(check.value)}
              </span>
            )}
            {check.interval && (
              <span className="check__interval">95% CI {interval(check.interval)}</span>
            )}
          </span>
          <span className="check__state">
            <span className={`chip chip--${check.state}`}>
              <span aria-hidden="true">{stateWord.glyph}</span> {stateWord.word}
            </span>
            <span className="check__threshold" data-testid={`threshold-${check.code}`}>
              {thresholdText(check)}
            </span>
          </span>
        </summary>
        <div className="check__detail">
          <p>{check.method ?? "No method recorded for this run."}</p>
          <p>{counts.map((row) => `${displayGroup(row.label)} ${row.n} rows`).join(" · ")}</p>
        </div>
      </details>
    </article>
  );
}

function Meaning({ result }: { result: Analysis }) {
  return (
    <div className="meaning">
      <p className="meaning__lead">{result.amplification.sentence}</p>
      <p className="meaning__detail">{result.amplification.detail}</p>
      {result.affected.map((row) => (
        <p key={row.group} className="meaning__detail" style={{ marginTop: 8 }}>
          {row.sentence}
        </p>
      ))}
      <div className="meaning__body">
        <p className="muted">{result.narrative.body}</p>
      </div>
    </div>
  );
}

export default function Report({ result }: { result: Analysis }) {
  const created = new Date(result.created_at).toISOString().slice(0, 10);
  return (
    <main className="report">
      <div className="report__main">
        <p className="small muted">
          {result.dataset.name} · {result.dataset.rows.toLocaleString("en-US")} rows · {created}
        </p>

        <Section id="verdict" index={0} title={SECTIONS[0].title}>
          <Verdict result={result} />
        </Section>

        <Section id="checks" index={1} title={SECTIONS[1].title}>
          <Checks result={result} />
        </Section>

        <Section id="affected" index={2} title={SECTIONS[2].title}>
          <Chart result={result} />
        </Section>

        <Section id="meaning" index={3} title={SECTIONS[3].title}>
          <Meaning result={result} />
        </Section>

        <Section id="method" index={4} title={SECTIONS[4].title}>
          <Technical result={result} />
        </Section>

        <footer className="report__foot small">
          <p>{result.privacy_line}</p>
          <p>{result.disclaimer}</p>
          <p className="faint">
            Template-generated narrative · engine {result.engine_version} · {result.duration_ms} ms
          </p>
        </footer>
      </div>

      <aside className="report__aside">
        <div className="aside__block">
          <p className="label">On this page</p>
          <ul className="aside__links">
            {SECTIONS.map((section, index) => (
              <li key={section.id}>
                <a href={`#${section.id}`}>
                  {pad(index)} {section.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
        <div className="aside__block">
          <p className="label">Dataset</p>
          <p className="aside__file">{result.dataset.name}</p>
          <p className="small muted">
            {result.dataset.rows.toLocaleString("en-US")} rows · {result.dataset.columns} columns
          </p>
          <p className="small muted">engine {result.engine_version}</p>
          <p className="small muted">{created}</p>
        </div>
      </aside>
    </main>
  );
}
