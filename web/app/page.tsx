export default function Home() {
  return (
    <main style={{ padding: "2rem", fontFamily: "system-ui" }}>
      <h1>FairLens v2 — Day Zero Probe</h1>
      <p>Probe app is live. The real UI starts at M0.</p>
      <ul>
        <li>
          <a href="/api/v1/health">Health check</a>
        </li>
        <li>
          <a href="/api/v1/dev/stream-probe">Stream probe</a>
        </li>
      </ul>
    </main>
  );
}
