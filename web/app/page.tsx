import SampleRunButton from "../components/SampleRunButton";

const SAMPLES = [
  {
    slug: "loan_approvals",
    name: "Loan approvals",
    description:
      "Real historical lending decisions, subsampled from UCI German Credit. A large recorded disparity.",
    expected: "Fail",
  },
  {
    slug: "hiring_shortlist",
    name: "Hiring shortlist",
    description:
      "Synthetic shortlisting data with moderate disparity and a proxy column a drop-repair cannot fix.",
    expected: "Warn",
  },
  {
    slug: "scholarship",
    name: "Scholarship awards",
    description:
      "Synthetic awards by region and age band. Fair by construction: all five checks pass.",
    expected: "Pass",
  },
];

export default function Home() {
  return (
    <main style={{ maxWidth: 880, margin: "0 auto", padding: "48px 24px", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 40, lineHeight: 1.1, marginBottom: 8 }}>FairLens</h1>
      <p style={{ color: "#55525C", marginBottom: 40 }}>
        Check a dataset before a model learns from it. Run a bundled sample — no account needed.
      </p>
      {SAMPLES.map((s) => (
        <section
          key={s.slug}
          data-testid={`card-${s.slug}`}
          style={{ borderTop: "1px solid #E3E0D8", padding: "24px 0", display: "flex", gap: 24, alignItems: "center", justifyContent: "space-between" }}
        >
          <div style={{ maxWidth: 560 }}>
            <h2 style={{ fontSize: 22, margin: "0 0 6px" }}>{s.name}</h2>
            <p style={{ color: "#55525C", margin: 0, fontSize: 15 }}>{s.description}</p>
            <p style={{ color: "#8A8794", margin: "8px 0 0", fontSize: 13, letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Expected: {s.expected}
            </p>
          </div>
          <SampleRunButton slug={s.slug} label="Run the analysis" />
        </section>
      ))}
    </main>
  );
}
