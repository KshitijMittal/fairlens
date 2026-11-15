# FairLens v2

**A fairness audit tool that tells you what your data would teach a model — before the model learns it.**

## What it does

Upload a CSV (or use one of the three bundled samples), confirm what the columns mean, and watch the analysis run. You get:

- A **verdict** — Fail / Warn / Inconclusive / Pass
- **Five checks** — Historical disparity, Model disparity, Amplification, Equal opportunity, Sample adequacy — each with a value, a 95% confidence interval, and a plain-language sentence
- **Who is affected** — the groups that are disadvantaged, by how much, with confidence intervals
- **Amplification** — whether the model widens, keeps, or narrows the gap the data already contains
- **Technical view** — per-group rates, TPR/FPR, model card, encoding, proxy scan
- **Repairs** — reweigh, resample, drop-proxies; each re-run on the re-uploaded file, compared side by side
- **Report** — short and full, print-ready, with a share link that can be revoked
- **Account** — password, Google sign-in, theme, delete with a cascade that leaves zero rows

## What it does NOT do

- No raw data is ever stored. The uploaded file is parsed, analysed, and discarded in one request.
- No model is trained on your data across users. Every analysis is independent.
- No third-party cookies, no tracking, no fingerprinting.
- No offline access, no refresh tokens — Google sign-in uses the standard code flow with PKCE.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Vercel (Next.js App Router)                │
│  /api/* → rewrite → Hugging Face Space      │
└────────────────────────────┬────────────────┘
                             │ HTTPS, response streamed
                             ▼
┌─────────────────────────────────────────────┐
│  Hugging Face Space (Gradio SDK, Free)      │
│  FastAPI inside Gradio, one uvicorn worker  │
│  All maths, all SQL, all secrets here       │
└────────────────────────────┬────────────────┘
                             │ psycopg3, TLS, pooled
                             ▼
┌─────────────────────────────────────────────┐
│  Neon Postgres (Free tier)                  │
│  Aggregates, text, tokens only              │
│  Never a row of the uploaded file           │
└─────────────────────────────────────────────┘
```

- **Frontend:** Next.js 14 (App Router), server components (report UI lands at M3)
- **Backend:** FastAPI, psycopg3 (pooled), scikit-learn, fairlearn, SHAP, 1000-resample bootstrap
- **Database:** Neon Postgres 16, 14 migrations, advisory lock at boot, immutable metrics
- **Auth (M2):** Email/password (argon2id), Google OAuth, Brevo HTTPS for password reset
- **Deployment:** Vercel Hobby (free), HF Space (ZeroGPU, free), Neon free tier

## Quick start (local)

```bash
# Prerequisites: Docker Desktop, Python 3.12+, Node 20+
git clone <repo>
cd fairlens

# Start local stack (Postgres on :5433, API on :7860)
docker compose up -d --build

# Run the unit tests (no database needed), from the repository root
.\.venv\Scripts\Activate.ps1
pytest -q --ignore=tests/integration

# Run the integration tests against the compose Postgres
# (TEST_DATABASE_URL must point at a disposable database: the suite recreates the schema)
$env:TEST_DATABASE_URL = "postgresql://fairlens:fairlens@localhost:5433/fairlens"
pytest tests/integration -q

# Frontend
cd web
npm install
npm run dev
# Open http://localhost:3000
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Pooled Postgres connection string |
| `DATABASE_URL_UNPOOLED` | Yes | Direct Postgres connection for migrations |
| `ENV` | No | `development` by default; `production` on the Space |
| `APP_ORIGIN` | Yes | Public web origin, used for reset links and the Google callback |
| `API_ORIGIN` | Yes (web) | Backend origin the server-rendered report page reads from; defaults to `http://localhost:7860` |
| `HF_TOKEN` | Deploy only | Hugging Face token; never read by the app |
| `GOOGLE_CLIENT_ID` | Optional | Google OAuth client; sign-in is hidden when unset |
| `GOOGLE_CLIENT_SECRET` | Optional | Google OAuth secret |
| `BREVO_API_KEY` | M2 | Brevo API key for password reset emails |
| `BREVO_SENDER` | M2 | Verified sender address in Brevo |
| `GEMINI_API_KEY` | M6 | AI narrative (optional; template works without) |
| `OPENROUTER_API_KEY` | M6 | Fallback AI provider |

Copy `.env.example` to `.env` and fill in values. The app starts in template-fallback mode if AI keys are missing.

## Project status

| Milestone | Status | Notes |
|---|---|---|
| **Day Zero** | ✅ Complete | Repo reset, five gates passed (G1–G4, G9) on free stack |
| **M0 — Walking Skeleton** | ✅ Complete | One sample analysed through deployed stack, tests passing |
| **M1 — Database** | ✅ Complete | 14 migrations, runner with advisory lock and checksum guard, repository, stored-payload read path, Docker + compose, 12 integration tests green. Deployed: live `/v1/health` reports `"database": true`, samples return pass/fail/warn, Neon holds 14 migrations |
| **M2 — Accounts, Upload, Confirmation** | ✅ Complete locally | Signup/login/logout, sessions, `/v1/me`, Google OAuth, password reset, upload guards, confirmation card with refusal, sampling and XLSX sheet choice, streamed six-stage log with `ping`, buffered fallback. 70 unit + 23 integration tests and 3 Playwright specs pass locally; Space deployment pending |
| **M3 — Verdict Interface** | ⏳ Pending | Report UI, charts, technical view |
| **M4 — Repairs** | ⏳ Pending | Three strategies, comparison, downloads |
| **M5 — Report, Share, History, Account** | ⏳ Pending | Print, share links, history, account management |
| **M6 — Narrative & Chat** | ⏳ Pending | AI narrative with guard, chat with citations |
| **M7 — Verification** | ⏳ Pending | CI contract, image, accessibility, preview deployments |
| **M8 — Hardening** | ⏳ Pending | Rate limits, keep-alive, privacy page, startup secrets |

### Cut line items dropped (per plan IP5)

| Order | Item | Milestone | Reason |
|---|---|---|---|
| 1 | Chat | M6 | Narrative and report survive |
| 2 | Google sign-in | M2 | Email/password and reset remain |
| 3 | Repairs | M4 | Verdict, report, technical view survive |

**Never dropped:** the five checks and their intervals, the four lead blocks and their copy, upload and confirmation, report and print, account deletion with its cascade test.

## Documentation

- `docs/PRD.md` — Product Requirements Document
- `docs/TRD.md` — Technical Requirements Document
- `docs/APP_FLOW.md` — App flow, routes, states, transitions
- `docs/UI_UX.md` — Visual design, copy, components, accessibility
- `docs/BACKEND_SCHEMA.md` — Database schema, migrations, queries, payload contract
- `docs/IMPLEMENTATION_PLAN.md` — Milestones, tests, cut line, risks, done definition
- `samples/README.md` — Bundled samples, sources, licences, perturbations

## Licence

MIT.

---

*FairLens v2 — built for the PRD, tested by the plan, deployed on free infrastructure.*