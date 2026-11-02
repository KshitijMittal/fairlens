# FairLens v2 — Implementation Plan

| | |
|---|---|
| **Version** | 1.3 (2 Nov: Day Zero complete; G1–G4 and G9 recorded in §2.2) |
| **Status** | Decisions closed (5 of 5). Day Zero complete. M0 next. |
| **Date** | 30 October 2026 |
| **Baseline** | `docs/PRD.md` v2.3, `docs/TRD.md` v2.4, `docs/APP_FLOW.md` v2.3, `docs/UI_UX.md` v2.2, `docs/BACKEND_SCHEMA.md` v2.2 |
| **Relationship to the TRD** | TRD §13.2 names the milestones. This document makes each one executable: files, commands, tests, and what to drop |

---

## 0. How to read this document

- **Section 1** is the five decisions, and the one thing each one changes.
- **Section 2** is day zero: the only destructive step in the project, then five gates that must be proven before any feature work. Nothing here is optional.
- **Section 3** is the target repository shape.
- **Section 4** is M0–M8. Each milestone has a goal, what it builds, an exit check you can run, the tests it adds, and what to drop if it runs long.
- **Section 5** is the v1 disposition table.
- **Section 6** maps every App Flow transition and every PRD acceptance criterion to a named test.
- **Sections 7–9** are the cut line, the risks this plan adds, and the definition of done.

The plan is executable in order. If two sections disagree, this document is wrong, not the baseline — fix it here.

---

## 1. The five decisions

| # | Decision | What it changes |
|---|---|---|
| **IP1** | Walking skeleton first | M0 ends with one sample analysed through the deployed stack. The milestones are the TRD's, made concrete |
| **IP2** | v1 is deleted outright; git starts empty | Day zero destroys the old app, then `git init`. The first commit contains v2 only. Nothing is ported |
| **IP3** | TRD gates G1–G4 plus **G9**, this plan's addition: a timed run on the real host | Day zero is half a day, and M0 does not start until G9 has a recorded number |
| **IP4** | Every milestone ships its own tests | M7 verifies; it does not write the suite |
| **IP5** | Fixed cut line: chat → Google → repairs | A milestone that runs long drops the named item instead of quietly taking a week longer |

---

## 2. Day zero

### 2.1 Clear the old version

The v1 app is not amended and not kept in the tree (PRD, header). The destruction is deliberate and happens once.

| Step | Command | Result |
|---|---|---|
| 1. Snapshot | `Compress-Archive app.py,modules,requirements.txt,.env.example,README.md "$env:TEMP\fairlens-v1.zip"` | A zip outside the repository, not in any commit, kept until v2 ships |
| 2. Delete | `Remove-Item -Recurse -Force app.py,modules,requirements.txt,__pycache__,README.md` | The working tree has no v1 code; the README is rewritten at M0 |
| 3. Initialise | `git init; git add -A; git commit -m "chore: start FairLens v2"` | History begins at v2. There is no v1 commit to revert to |
| 4. Protect | `.gitignore` covers `venv/`, `node_modules/`, `.next/`, `.env`, `__pycache__/`, `*.pyc` | The 26,000-file virtualenv never enters history |

**Rules**

- The snapshot is a zip, not a branch. It exists to recover a formula in an emergency, not to compare implementations.
- `.env` is never committed; `.env.example` is committed at day zero with every secret blank, and M0 keeps its names in sync with the settings model.
- Step 2 happens before step 3. A repository that contains both versions invites "just fix it in the old one".

### 2.2 The gates

A gate is passed by a recorded measurement, not an opinion. Each row names the command, the pass condition, and what is done when it fails. All five run on the deployed free stack, not on localhost.

| # | Question | Command | Pass | If it fails |
|---|---|---|---|---|
| **G1** | Does the Vercel rewrite pass an NDJSON stream through unbuffered? | `curl.exe -N https://<app>/v1/dev/stream-probe` | Three frames arrive spread over at least two seconds | Ship with `NEXT_PUBLIC_ANALYSIS_STREAMING=0`: one JSON body and a spinner. The verdict is unchanged |
| **G2** | Can the Space send reset mail? Spaces allow only ports 80, 443 and 8080, so there is no SMTP | `python backend/scripts/mail_probe.py https://<space> you@example.com` | The message arrives | Brevo is the design, not a fallback. If the sender is rejected, verify it in Brevo; the app still starts and logs the failure |
| **G3** | Does a 60 MB body survive the rewrite? | `curl.exe -F "file=@samples/_gate/big.csv" https://<app>/v1/dev/echo-size` | The endpoint reports 62,914,560 bytes | Uploads go direct to the Space with a one-time ticket. This is the expensive fallback and the reason the gate is on day zero |
| **G4** | Do SHAP and fairlearn install and import on the Space's Python? | Push the probe, then `curl.exe https://<space>/v1/health` | Both versions are reported; neither says `unavailable` | Pin Python 3.11 in the Space's README. If SHAP still fails, influence is marked unavailable (F3-AC5) and the verdict is unaffected |
| **G9** | Can the host run the pipeline's heaviest operations inside the budget? | `python backend/scripts/bench_host.py https://<space>`: a synthetic 50,000 × 60 frame, CSV round-trip, 5-fold logistic regression, 1,000 bootstrap resamples, SHAP on 500 rows | Warm under **20 s** (F3-AC6) and every run under **55 s** (TRD §6.1). Cold and warm both recorded | Reduce the SHAP sample from 500 to 200 rows. If still over, the sampling offer becomes mandatory at 25,000 rows — a PRD change, not a silent tweak |

**Recorded result.** The five outcomes go into the table below before M0 begins: date, host, numbers, fallback taken or not. A gate with no recorded number has not been run.

| Gate | Date | Host | Measurement | Fallback taken |
|---|---|---|---|---|
| G1 | 2026-11-01 | Vercel rewrite → Space (`web-sigma-roan-24.vercel.app/api/v1/dev/stream-probe`) | 3 NDJSON frames at 1.29 / 1.80 / 2.31 s (~0.5 s apart), `application/x-ndjson` preserved; unbuffered | none |
| G2 | 2026-11-01 | Space → Brevo HTTPS API | `mail_probe.py` returns 202; message received at the verified sender's inbox | none (Brevo IP restriction disabled — Spaces egress IPs are dynamic and cannot be whitelisted) |
| G3 | 2026-11-01 | Vercel rewrite → Space (`/api/v1/dev/echo-size`) | reports 62,914,560 bytes; HTTP 200 in 13.6 s | none |
| G4 | 2026-11-01 | `kshitijmittal07-fairlens-probe.hf.space` (ZeroGPU, Python 3.12.12) | `/v1/health` reports shap 0.54.1, fairlearn 0.15.0; neither `unavailable` | none |
| G9 | 2026-11-01 | `kshitijmittal07-fairlens-probe.hf.space` (ZeroGPU) | `bench_host.py`: cold 5.4 s, warm 5.56 s (budget 55 s / 20 s) | none |

**Time box: half a day.** The probe deploy is the thinnest possible application: `/v1/health`, `/v1/dev/stream-probe`, `/v1/dev/echo-size`, `/v1/dev/bench`, `/v1/dev/mail-probe`, and a page that renders one line. It is thrown away at M0 and rebuilt properly, which is cheaper than discovering G3 after the upload component exists.

---

## 3. Target repository shape

```
fairlens/
├─ backend/
│  ├─ Dockerfile                local compose image only; the host never builds it
│  ├─ pyproject.toml
│  ├─ space/                    the Gradio Space: app.py, requirements.txt, README.md
│  └─ app/
│     ├─ main.py                 FastAPI app, middleware, routers
│     ├─ core/                   settings, verdict, report_text, security
│     ├─ api/                    auth, analyses, repairs, shares, account
│     ├─ db/
│     │  ├─ migrations/          0001–0014, numbered, applied at boot
│     │  └─ queries/             one named .sql file per statement
│     └─ services/               parsing, encoding, model, metrics, influence, narrative
├─ web/
│  ├─ app/                       Next.js App Router routes from App Flow §2
│  ├─ components/                shadcn/ui copies plus the report components
│  ├─ lib/                       generated API client, theme resolution
│  └─ e2e/                       Playwright specs named in §6
├─ samples/                      the three bundled CSVs, also the test fixtures
├─ scripts/                      bench_host.py, mail_probe.py, seed.py
├─ .github/workflows/            ci.yml, keep-alive.yml
├─ docker-compose.yml            postgres:16 + api + web
└─ docs/                         these six documents
```

**Three rules the tree enforces by shape**

- No TypeScript file computes a figure. Every sentence containing one arrives from `backend/app/core/report_text.py` and the payload, and the client renders it verbatim (PRD F4-AC6).
- No SQL lives in a TypeScript file or in a Python string. Every statement is a file in `db/queries/` (TRD T9).
- `samples/` is imported by both the API and the tests, so a sample that stops producing its documented verdict fails the build rather than the demo (F11-AC5).

---

## 4. The milestones

Each milestone ends with something deployed and a command that proves it. "Done" means the exit check passes **and** the tests listed in that milestone are in the same change (IP4).

### 4.0 Two reconciliations applied to TRD §13.2

Both are consequences of decisions taken later, and both are now written into the TRD:

1. **The cascade test moves from M8 to M1.** Account deletion is on the never-cut list, and F9-AC1 is the privacy promise. Leaving its test at M8 means the promise is unverified for seven milestones.
2. **M8's exit check is restated.** It no longer claims the deletion test; that test already runs from M1. M8 now proves rate limits, the keep-alive, and the privacy page.

---

### M0 — Walking skeleton

**Goal.** One bundled sample travels through the real engine and appears on a deployed page. No accounts, no upload, no database.

| Builds | Detail |
|---|---|
| Deploy | Hugging Face Space (Gradio SDK, FastAPI mounted) and Vercel (Next app) wired by the rewrite from TRD §9.1 |
| Health | `GET /v1/health` returns version and a database flag that is `false` at this milestone |
| Engine | Parsing for the bundled CSV, encoding, 5-fold logistic regression, C1–C5, bootstrap intervals. No SHAP yet |
| Payload | `AnalysisResult` with the server-authored sentences already in `report_text.py`, including the four lead headlines |
| Page | `/` runs a sample; `/analysis/[id]` renders the verdict banner and five check rows from the response only |
| No database | The result exists in the response and nowhere else. `/analysis/[id]` is server-rendered from a short-lived in-process cache keyed by the run id, and says so nowhere in the UI because the user never sees the difference. This cache survives M1 for anonymous sample runs only |

**Exit check**

```
curl.exe -s https://<app>/v1/health
curl.exe -s -X POST https://<app>/v1/dev/sample/scholarship | head -c 400
npx playwright test web/e2e/skeleton.spec.ts
```

The page shows `PASS` and all five checks for the scholarship sample.

**Tests added**

- `tests/test_golden_scholarship.py` — the sample produces Pass, five green checks, no Inconclusive, positives and negatives in every group (F11-AC3).
- `tests/test_golden_samples.py` — all three bundled files produce their documented verdicts, and are the same files the API serves (F11-AC1, F11-AC2, F11-AC5).
- `web/e2e/skeleton.spec.ts` — a sample click reaches a rendered verdict with no console error.
- `tests/test_report_text.py` — the four lead headlines and both forms of every check sentence match UI/UX §7.1–7.2 verbatim.
- `tests/test_no_row_data.py` — the serialised payload contains no cell value from the sample (the shape test from BACKEND_SCHEMA §3.1).

**If it runs long:** drop the second and third samples. One sample proves the path.

---

### M1 — Database

**Goal.** The result is stored, immutable, and readable exactly as the payload describes.

| Builds | Detail |
|---|---|
| Migrations | `0001`–`0014`, applied at boot under an advisory lock (TRD §12.1) |
| Queries | `analyses_insert`, `analyses_by_id`, `checks_by_analysis`, `groups_by_analysis` |
| Save | The `saving` stage writes analysis, checks and groups in one transaction; the narrative follows at the narration stage through `narrative_insert.sql` |
| Read | `GET /v1/analyses/{id}` assembles the same `AnalysisResult` from the tables, through one builder shared with the stream |
| History skeleton | `top_level_analyses` view plus a minimal list, no styling |

**Exit check**

```
docker compose up -d --build
pytest tests/integration -q
psql "$DATABASE_URL" -c "select count(*) from analyses"
```

**Tests added**

- `tests/integration/test_migrations.py` — all fourteen apply to an empty Postgres 16, and again from scratch.
- `tests/integration/test_cascade.py` — the ten-zero deletion test, including a repair child analysis (F9-AC1).
- `tests/integration/test_immutability.py` — `UPDATE` on each of the four tables raises `restrict_violation`; `DELETE` still cascades.
- `tests/integration/test_deciding_checks.py` — the §3.3 consistency query returns zero rows for a batch of fixtures.
- `tests/integration/test_top_level.py` — a child analysis does not appear in the history view.
- `tests/test_anonymous_cache.py` — an anonymous sample run writes zero rows and is still readable by its run id; after expiry the id 404s.
- `tests/test_roundtrip.py` — the stored result and the streamed result serialise identically (S8).

**If it runs long:** drop the history list. The report read is what proves the schema.

---

### M2 — Accounts, upload, confirmation

**Goal.** A real person can sign in, drop their own file, confirm what it means, and get a stored result.

| Builds | Detail |
|---|---|
| Auth | Signup, login, logout, sessions, `/v1/me`; Google as a second method; reset by Brevo HTTPS per G2 |
| Upload | 50 MB / 100,000 rows / 60 columns guards in the order of TRD §11.2; delimiter and encoding detection (F1-AC1) |
| Confirmation | Deterministic column detection, the one card, the `Change` disclosure, the five refusal cases (F2) |
| Choices | Sampling above 50,000 rows; XLSX sheet choice |
| Streaming | The six-stage NDJSON log, fold lines, `ping`, buffered fallback behind the env flag |

**Exit check**

```
curl.exe -s -o NUL -w "%{http_code}" -F "file=@samples/loans.csv" https://<app>/v1/analyses
# 401

curl.exe -s -b cookies.txt -F "file=@samples/loans.csv" https://<app>/v1/analyses --no-buffer
# stage frames, then result
```

**Tests added**

- `tests/test_parsing.py` — semicolon/Latin-1 equals comma/UTF-8 (F1-AC1); duplicate and empty-column counts (F1-AC5); corrupt file gives a sentence, not a traceback (F1-AC6).
- `tests/test_sampling.py` — seeded, repeatable, recorded in the payload and the JSON (F1-AC4, F1-AC7).
- `tests/test_detection.py` — the three samples prefill correctly with no input (F2-AC1); single-value column blocks (F2-AC4); majority class wins the default (F2-AC3).
- `tests/integration/test_auth.py` — unauthenticated upload is 401 (F8-AC5); reset token single-use, 30 minutes, invalidated by password change (F8-AC2); uniform reset response (F8-AC3).
- `tests/test_log_hygiene.py` — no password or token in captured logs (F8-AC4).
- `tests/test_startup.py` — a production boot with a sensitive Google scope configured fails loudly (F8-AC1). M8 extends this file to the reset sender and pepper.
- `web/e2e/upload.spec.ts` — drop → confirm → run → report; the URL changes only on result (A1).
- `web/e2e/anonymous.spec.ts` — signed-out dropzone triggers no upload request (A2).

**If it runs long:** Google sign-in goes (it is second on the cut line). Email and password stay.

---

### M3 — The verdict interface

**Goal.** The report looks like `UI_UX.md` and every figure on it exists in the payload.

| Builds | Detail |
|---|---|
| Tokens | Type scale, spacing, both palettes, theme resolved from the cookie with no script |
| Lead blocks | The four states with their exact copy; Inconclusive names the check that could not be judged |
| Checks | Five rows, states, intervals, thresholds, never-collapsed Inconclusive |
| Chart | Selection rate by group, historical vs model, one SVG component |
| Affected | Server sentences naming the real groups and the gap |
| Technical view | Metric table, per-group table, model card, encoding, influence, proxies, sampling record |
| Motion | The reveal sequence, `prefers-reduced-motion` honoured |

**Exit check**

```
npx playwright test web/e2e/verdicts.spec.ts
npx axe web/e2e --tags wcag2a,wcag2aa
```

Four fixtures — one per verdict — each render their own lead block and identical skeletons.

**Tests added**

- `web/e2e/verdicts.spec.ts` — four states, four headlines, no fifth (F4-AC1).
- `web/e2e/traceability.spec.ts` — every number in the summary appears in the technical view (F4-AC2) and in the payload (F3-AC7).
- `web/e2e/inconclusive.spec.ts` — never pass-coloured, never collapsed (F4-AC3).
- `tests/test_report_text.py` extended — every Inconclusive check carries one of the four reason phrases from PRD §8.4, verbatim.
- `tests/test_influence.py` — SHAP failure returns influence as unavailable and leaves the verdict and repair numbers unchanged (F3-AC5).
- `web/e2e/theme.spec.ts` — correct theme in the first paint, no flash, works with JavaScript disabled.
- `web/e2e/contrast.spec.ts` — the eight verdict pairs plus ink on paper, both themes (UI_UX A15).

**If it runs long:** motion. The report is complete without it; the reveal is the only thing that may be dropped here, and it is not on the cut line.

---

### M4 — Repairs

**Goal.** The three strategies run on a re-supplied file, produce comparable numbers, and download.

| Builds | Detail |
|---|---|
| Strategies | Reweigh, resample, drop-proxies, identical folds and seed (F6-AC2) |
| Evidence | Fingerprint check against `source_sha256`; refusal on mismatch. A sample needs no check because the server already holds the CSV |
| Comparison | One table, server-authored summary per row, recommendation rule (2-point accuracy floor) |
| Downloads | CSV per strategy, generated on demand, never stored |
| Refresh | `DELETE` + `INSERT` in one transaction, for the comparison rows and the three child analyses; no `UPDATE` |

**Exit check**

```
pytest tests/test_repairs.py -q
curl.exe -s -b cookies.txt -F "file=@samples/loans.csv" https://<app>/v1/analyses/<id>/repairs
```

Two runs on the same file produce identical CSV hashes (F6-AC7).

**Tests added**

- `tests/test_repairs.py` — row/column shape per strategy (F6-AC1); identical folds (F6-AC2); removed columns named (F6-AC3); accuracy floor respected (F6-AC4); no recommendation when nothing helps (F6-AC5); same hash twice (F6-AC7).
- `tests/integration/test_repairs_refresh.py` — a second run leaves exactly three comparison rows and three child analyses, and no update succeeds.
- `web/e2e/repairs.spec.ts` — file absent → picker → fingerprint check → comparison; wrong file is refused with both fingerprints.

**If it runs long:** drop-proxies goes, but the cut line says repairs last — so this is the milestone that must absorb slippage rather than pass it on.

---

### M5 — Report, share, history, account

**Goal.** The verdict can leave the building, and the owner can see and remove what is stored.

| Builds | Detail |
|---|---|
| Print | Short and full reports; light palette forced; greyscale legible |
| Share | Create, list, revoke; token hash only; 404 after revoke |
| History | Rows with dataset, date, verdict, deciding checks; samples filter; delete with confirm |
| Account | Password change, theme preference, delete account with counts from one query |

**Exit check**

```
npx playwright test web/e2e/share.spec.ts web/e2e/history.spec.ts web/e2e/account.spec.ts
```

A revoked token 404s on the next request; history renders after the file is gone.

**Tests added**

- `web/e2e/share.spec.ts` — signed-out viewer sees the same figures (F7-AC1); revoke is immediate (F7-AC2); no row data reachable (F7-AC3).
- `web/e2e/print.spec.ts` — one document, no navigation, no clipped chart (F7-AC4), footer present (F7-AC5).
- `web/e2e/history.spec.ts` — delete removes the row and kills its links (F9-AC2); samples filter; a signed-in sample run gets a chip (A8).
- `web/e2e/account.spec.ts` — typed phrase gates deletion; counts match the categories; deletion signs out (F9-AC3).
- `web/e2e/theme.spec.ts` — account switch applies across a reload, with no flash (App Flow transition 30).
- `tests/integration/test_account_delete.py` — the API path leaves zero rows, not only the direct SQL path.

**If it runs long:** the samples filter. Everything else here is on the never-cut list or is how the report travels.

---

### M6 — Narrative and chat

**Goal.** Prose that cannot invent a number, with a complete fallback when no model is reachable.

| Builds | Detail |
|---|---|
| Narrative | AI or template, labelled; cached by result hash and `prompt_version` |
| Guard | Output rejected or stripped if it contains a figure not in the payload (F10-AC1) |
| Chat | Scoped to the analysis, cites stored metric keys, refuses anything else |
| Cache | Second open makes zero calls (F10-AC6) |

**Exit check**

```
pytest tests/test_llm_guard.py -q
curl.exe -s -b cookies.txt https://<app>/v1/analyses/<id> | grep -c '"provider"'
```

**Tests added**

- `tests/test_llm_guard.py` — a prompt engineered to emit `42%` is rejected or stripped (F10-AC1); an injected column header does not change the narrative (F10-AC5).
- `tests/integration/test_llm_cache.py` — re-open makes zero provider calls (F10-AC6); a `prompt_version` bump misses the cache for a new run, while a stored narrative is unchanged.
- `web/e2e/narrative.spec.ts` — no key configured → full report, labelled template (F4-AC4, F10-AC2); mid-session provider failure leaves no partial report (F10-AC3).
- `tests/test_chat_scope.py` — an unrelated question is refused, naming the analysis (F10-AC4).

**If it runs long:** chat goes first, then the AI narrative (template stays).

---

### M7 — Verification

**Goal.** Prove the contract, the image and the interface, without writing new coverage.

| Builds | Detail |
|---|---|
| Contract | Commit `openapi.json`; generated client compiles; `git diff --exit-code` |
| Image | CI builds, boots, migrates and analyses one sample |
| Browser | Full Playwright suite against compose, axe on four states and login |
| Preview | Per-PR Vercel preview against the production API, as TRD §12.4 states |
| Logs | The hygiene test runs in CI, not only locally |

**Exit check**

```
pytest -q && npm --prefix web run test:e2e && git diff --exit-code -- openapi.json
```

**Tests added:** none. This milestone makes existing tests blocking in CI and removes the ones that were scaffolding.

**If it runs long:** previews. Contract, image and axe are the three that catch real breakage.

---

### M8 — Hardening

**Goal.** Survive a stranger, a cold start, and a week of nobody visiting.

| Builds | Detail |
|---|---|
| Limits | The UPSERT counters, per-IP and per-account, 429 with retry-after (F12) |
| Keep-alive | Fourteen-minute `/v1/health` ping that also warms the database |
| Privacy page | The claims in PRD §10, each one true of the code |
| Secrets | Startup refuses a production boot with a missing sender or pepper (F8-AC6) |
| Sweeps | Expired sessions, used reset tokens, old rate-limit windows |

**Exit check**

```
for i in $(seq 1 7); do curl.exe -s -o NUL -w "%{http_code} " -F "file=@samples/loans.csv" https://<app>/v1/analyses; done
# 401 401 401 401 401 429 429

curl.exe -s https://<app>/v1/health
```

**Tests added**

- `tests/integration/test_rate_limit.py` — the sixth anonymous request is 429 with retry-after (F12-AC1); a direct API call is limited identically (F12-AC2); no analysis row is created (F12-AC3).
- `tests/test_upload_guard.py` — 50 MB rejected from `Content-Length` before reading (F12-AC4).
- `tests/test_startup.py` — production boot without a sender or pepper fails loudly (F8-AC6).

**If it runs long:** the sweeps. They cost storage, not correctness, and the counters expire on their own.

---

## 5. v1 disposition

The old app is deleted, not amended (PRD header, IP2). Every row is a deletion; the reason is what the replacement is.

| File | Disposition | Why |
|---|---|---|
| `app.py` | Delete | One Streamlit script held navigation, state, upload, report and chat. v2 splits these across routes and the API |
| `modules/column_detector.py` | Delete | Name-list heuristics are reimplemented in the parser with cardinality checks (F2) |
| `modules/data_loader.py` | Delete | Replaced by the delimiter/encoding parser with the 50 MB and 100,000-row guards (F1) |
| `modules/fairness_calculator.py` | Delete | Uses a single-score framing and no intervals; v2 computes five checks with bootstrap CIs (PRD §8) |
| `modules/model_trainer.py` | Delete | No out-of-fold predictions; v2 requires them (F3-AC2) |
| `modules/mitigator.py` | Delete | Reweighing is rewritten against the new engine and fold assignment (F6-AC2) |
| `modules/explainer.py` | Delete | SHAP stays as a feature; the implementation is replaced and becomes optional (F3-AC5) |
| `modules/report_generator.py` | Delete | Gemini prompt replaced by `report_text.py` and the narrative guard (F4-AC6, F10-AC1) |
| `modules/__init__.py` | Delete | The package goes with its contents |
| `requirements.txt` | Delete | v2 dependencies live in `backend/pyproject.toml` and `web/package.json` |
| `README.md` | Rewrite | Describes v2, how to run it, and what it does not claim |
| `.env` / `.env.example` | Rewrite | New variables, every value blank, template fallback works with none set |
| `assets/`, `data/`, `__pycache__/` | Delete | Nothing references them; the samples move to `samples/` |

**Nothing is ported.** The two genuinely fiddly pieces — the demographic name lists and the reweighing weights — are rewritten in M2 and M4 and covered by the tests named above, which is cheaper than adapting code written without intervals or folds.

---

## 6. Test map

### 6.1 Every App Flow transition

Each row is one transition from App Flow §5. The test name is the file and the case that must fail if the transition breaks.

| # | Transition | Test |
|---|---|---|
| 1 | `/` signed out → sample → confirmation card | `landing.spec.ts › sample prefills the card` |
| 2 | `/` signed out → sign-in line → `/login` | `landing.spec.ts › anonymous dropzone routes to login` |
| 3 | `/login` → success → `/` signed in | `auth.spec.ts › login lands idle` |
| 4 | `/` signed in → file dropped → inspecting | `upload.spec.ts › drop enters inspecting` |
| 5 | inspecting → inspect ok → confirmation | `upload.spec.ts › valid file shows card` |
| 6 | inspecting → inspect failed → error, file kept | `upload.spec.ts › corrupt file keeps the file` |
| 7 | inspecting → over 50k → sampling choice | `upload.spec.ts › large file offers sample` |
| 8 | inspecting → XLSX several sheets → sheet choice | `upload.spec.ts › sheet picker appears` |
| 9 | confirmation → Change → changing | `upload.spec.ts › change reveals selectors` |
| 10 | confirmation → run → running | `upload.spec.ts › run starts the log` |
| 11 | changing → run → running | `upload.spec.ts › run from changing uses the edits` |
| 12 | confirmation → cancel → idle | `upload.spec.ts › cancel returns to idle` |
| 13 | running → stage → next line | `stream.spec.ts › stage frames append` |
| 14 | running → result → `/analysis/{id}` | `stream.spec.ts › result navigates once` |
| 15 | running → error → run failed | `stream.spec.ts › error frame shows panel` |
| 16 | running → cancel → confirmation | `stream.spec.ts › cancel aborts and restores` |
| 17 | run failed → retry → running | `stream.spec.ts › retry per class` |
| 18 | run failed → another file → idle | `stream.spec.ts › another file clears` |
| 19 | run failed → unauthenticated → login, file lost | `auth.spec.ts › expired session on run` |
| 20 | report → short print | `print.spec.ts › short report` |
| 21 | report → full print | `print.spec.ts › full report expands technical` |
| 22 | report → JSON | `report.spec.ts › json downloads the payload` |
| 23 | report → create share | `share.spec.ts › link row appears` |
| 24 | report → revoke | `share.spec.ts › revoke removes row` |
| 25 | repair, file in memory → running → complete | `repairs.spec.ts › in-memory path` |
| 26 | repair, file absent → needs file → checking → running | `repairs.spec.ts › re-upload path` |
| 27 | `/history` → open → `/analysis/{id}` | `history.spec.ts › open a row` |
| 28 | `/history` → delete → confirm → removed | `history.spec.ts › delete row and links` |
| 29 | `/shared/{token}` → any → stays | `share.spec.ts › shared page has no navigation` |
| 30 | `/account` → theme changed → re-rendered | `theme.spec.ts › account switch applies` |
| 31 | any authed route → session expired → login | `auth.spec.ts › expiry returns to login` |

### 6.2 Every acceptance criterion

Each feature's criteria are asserted in the file named against it; a criterion with no assertion is a defect in this plan.

| Feature | Milestone | Test file |
|---|---|---|
| F1 upload and ingest | M2 | `tests/test_parsing.py`, `tests/test_sampling.py`, `web/e2e/upload.spec.ts` |
| F2 confirmation | M2 | `tests/test_detection.py`, `web/e2e/upload.spec.ts` |
| F3 run the analysis | M0–M3 | `tests/test_golden_*.py`, `tests/test_roundtrip.py`, `tests/test_influence.py`, `web/e2e/traceability.spec.ts` |
| F4 summary view | M3 | `web/e2e/verdicts.spec.ts`, `web/e2e/traceability.spec.ts`, `web/e2e/inconclusive.spec.ts` |
| F5 technical view | M3 | `web/e2e/traceability.spec.ts`, `web/e2e/report.spec.ts`, `tests/test_influence.py` |
| F6 repairs | M4 | `tests/test_repairs.py`, `web/e2e/repairs.spec.ts` |
| F7 report, share, print | M5 | `web/e2e/share.spec.ts`, `web/e2e/print.spec.ts` |
| F8 accounts | M2, M8 | `tests/integration/test_auth.py`, `tests/test_log_hygiene.py`, `tests/test_startup.py` |
| F9 history and deletion | M1, M5 | `tests/integration/test_cascade.py`, `tests/test_anonymous_cache.py`, `web/e2e/history.spec.ts`, `web/e2e/account.spec.ts` |
| F10 narrative and chat | M6 | `tests/test_llm_guard.py`, `tests/test_chat_scope.py`, `tests/integration/test_llm_cache.py`, `web/e2e/narrative.spec.ts` |
| F11 bundled samples | M0, M7 | `tests/test_golden_scholarship.py`, `tests/test_golden_samples.py` |
| F12 abuse protection | M8 | `tests/integration/test_rate_limit.py`, `tests/test_upload_guard.py` |

### 6.3 The three tests that protect the documents

These exist because a passing product can still make the documents false.

| Test | Asserts | Protects |
|---|---|---|
| `test_report_text.py` | The four lead headlines, both forms of every check sentence, and the Inconclusive reason sentences match UI/UX §7 verbatim | The copy cannot drift from the specification |
| `test_deciding_checks.py` | The stored array equals the check rows that decided the verdict | BACKEND_SCHEMA §3.3 |
| `test_no_row_data.py` | The serialised payload contains no cell value, and no new column can hold one without appearing on the approved list | PRD §10 and BACKEND_SCHEMA §3.1 |

---

## 7. The cut line

IP5, written here so a long milestone has an answer that is not "work later".

| Order | Dropped | What survives |
|---|---|---|
| 1 | **Chat** (F10 chat half) | The narrative, template or AI, and the whole report |
| 2 | **Google sign-in** (F8 alternative) | Email and password, reset, sessions |
| 3 | **Repairs** (F6) | The verdict, the report, the technical view, the downloads of the result |

**Never dropped, in any circumstance:** the five checks and their intervals, the four lead blocks and their copy, upload and confirmation, report and print, account deletion with its cascade test.

A dropped item is recorded in the README's status section and in this table, with the milestone that dropped it. It is not deleted from the PRD.

---

## 8. Risks this plan adds

| # | Risk | Where it bites | Response |
|---|---|---|---|
| P1 | **G9 measures the host, not the engine.** A synthetic workload proves the CPU and memory story; the real pipeline can still be slower | M0, M3 | M0 times the real sample without influence; M3's exit check re-times it with SHAP enabled. Either miss fails the milestone |
| P2 | **The in-process result cache has no eviction.** It is the only home of an anonymous sample run, so it is never removed entirely | M0 onward | One worker process (TRD §4), a hard cap of 50 entries and a 30-minute TTL; an expired id shows the not-found page. Never hardened beyond that |
| P3 | **M2 is the largest milestone.** Auth, upload, confirmation and streaming in one step | M2 | The cut line applies at the first sign of slippage; Google leaves before anything else |
| P4 | **The plan writes no dates.** A milestone can sit "in progress" indefinitely | whole build | Each milestone's exit check is a command. A milestone with no green command is not in progress, it is stuck |
| P5 | **Copy and maths ship together** (S6). A wording fix is a backend deploy | M3 onward | Accepted and recorded; the verbatim test is what keeps the documents honest |

---

## 9. Definition of done

The project is finished when all of the following are true at once.

1. The three samples produce their documented verdicts through the deployed stack, and the golden tests are blocking in CI.
2. Every transition in §6.1 has a passing test, and every acceptance criterion in §6.2 has an assertion.
3. The deletion test leaves ten zeros, including a repair child.
4. A 50,000-row, 60-column file finishes warm under 20 seconds on the free host, and no run exceeds 55 seconds.
5. Printing produces one legible document in greyscale, in the light palette.
6. `docs/` contains no statement contradicted by the code, and the three tests in §6.3 are green.
7. `README.md` states what the product does, what it does not claim, and which cut-line items were dropped.

---

*End of Implementation Plan v1.1. This is the sixth and last document; the build starts at §2.1.*

