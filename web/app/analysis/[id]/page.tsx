import { notFound } from "next/navigation";

const STATE_WORDS: Record<string, { word: string; glyph: string; fg: string; tint: string }> = {
  fail: { word: "FAIL", glyph: "✕", fg: "#8C2F2A", tint: "#FBEDEB" },
  warn: { word: "WARN", glyph: "!", fg: "#8A5A12", tint: "#FBF3E4" },
  inconclusive: { word: "INCONCLUSIVE", glyph: "?", fg: "#3E4C63", tint: "#EEF1F6" },
  pass: { word: "PASS", glyph: "✓", fg: "#1F5A3D", tint: "#EAF3ED" },
};

export default async function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const origin = process.env.API_ORIGIN ?? "http://localhost:7860";
  const res = await fetch(`${origin}/v1/analyses/${id}`, { cache: "no-store" });
  if (!res.ok) {
    notFound();
  }
  const result = await res.json();
  const state = STATE_WORDS[result.verdict];

  return (
    <main style={{ maxWidth: 880, margin: "0 auto", padding: "48px 24px", fontFamily: "system-ui" }}>
      <p style={{ color: "#8A8794", fontSize: 13, letterSpacing: "0.06em", textTransform: "uppercase" }}>
        {result.dataset.name} — {result.dataset.rows} rows
      </p>
      <section
        data-testid="verdict-banner"
        style={{ background: state.tint, color: state.fg, padding: 32, borderRadius: 2, marginTop: 16 }}
      >
        <p style={{ margin: 0, fontSize: 13, letterSpacing: "0.06em" }}>
          {state.glyph} {state.word}
        </p>
        <h1 data-testid="verdict-headline" style={{ fontSize: 40, lineHeight: 1.1, margin: "12px 0" }}>
          {result.lead.headline}
        </h1>
        <p style={{ margin: 0, fontSize: 17, lineHeight: 1.6 }}>{result.lead.consequence}</p>
      </section>

      <section style={{ marginTop: 48 }}>
        <h2 style={{ fontSize: 30, margin: "0 0 16px" }}>The five checks</h2>
        {result.checks.map((check: any) => {
          const checkState = STATE_WORDS[check.state];
          return (
            <div
              key={check.code}
              data-testid={`check-${check.code}`}
              style={{ borderTop: "1px solid #E3E0D8", padding: "20px 0", display: "grid", gridTemplateColumns: "1fr auto", gap: 8 }}
            >
              <div>
                <p style={{ margin: 0, color: "#8A8794", fontSize: 13, letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  {check.code}
                  {check.core ? " · core" : ""} — {check.name}
                </p>
                <p style={{ margin: "6px 0 0", color: "#55525C", fontSize: 15 }}>{check.sentence}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ margin: 0, color: checkState.fg, fontWeight: 600 }}>
                  {checkState.glyph} {checkState.word}
                </p>
                {check.value !== null && (
                  <p style={{ margin: "4px 0 0", fontSize: 22 }}>
                    {check.value}
                    {check.interval ? (
                      <span style={{ color: "#55525C", fontSize: 13 }}> (CI {check.interval[0]}–{check.interval[1]})</span>
                    ) : null}
                  </p>
                )}
                <p style={{ margin: "4px 0 0", color: "#8A8794", fontSize: 13 }}>
                  {check.threshold.pass_at !== undefined && `pass ≥ ${check.threshold.pass_at}`}
                  {check.threshold.warn_at !== undefined && ` · warn ${check.threshold.warn_at}`}
                  {check.threshold.min_group_rows !== undefined && `n ≥ ${check.threshold.min_group_rows}`}
                </p>
              </div>
            </div>
          );
        })}
      </section>

      <section style={{ marginTop: 48 }}>
        {result.affected.length > 0 && <h2 style={{ fontSize: 30, margin: "0 0 16px" }}>Who is affected</h2>}
        {result.affected.map((a: any) => (
          <p key={a.group} style={{ fontSize: 17, lineHeight: 1.6 }}>{a.sentence}</p>
        ))}
        <p style={{ fontSize: 17, lineHeight: 1.6 }}>{result.amplification.detail}</p>
      </section>

      <footer style={{ marginTop: 64, paddingTop: 16, borderTop: "1px solid #E3E0D8", color: "#55525C", fontSize: 14 }}>
        <p style={{ margin: 0 }}>{result.narrative.body}</p>
        <p style={{ margin: "12px 0 0", color: "#8A8794" }}>
          Template-generated narrative · engine {result.engine_version} · {result.duration_ms} ms
        </p>
      </footer>
    </main>
  );
}
