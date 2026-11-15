# FairLens v2 — Technical Requirements Document

| | |
|---|---|
| **Version** | 2.4 (30 Oct: backend runs on a free Gradio Space; password reset by Brevo HTTPS, no SMTP) |
| **Status** | All 10 decisions closed. Implementation Plan written. |
| **Date** | 26 October 2026 |
| **Baseline** | `docs/PRD.md` v2.3 — every decision here exists to satisfy a feature or acceptance criterion there |
| **Supersedes** | The v1 Streamlit application and its `modules/` package |
| **Next document** | `docs/IMPLEMENTATION_PLAN.md` (written; a change here requires a matching change there) |

---

## 0. How to read this document

- **Sections 1–3** are the shape of the system: what runs where, and the order in which one click turns into a verdict.
- **Sections 4–10** are the buildable core: data access, auth, the analysis pipeline, the streaming contract, the HTTP API, the frontend, and shared state.
- **Sections 11–14** are how it is kept safe, deployed and tested.
- **Section 15** is the risk register, and it is the section to read on day one of the build, because four of its items are cheap to check now and expensive to discover in week three.
- Every decision has an identifier (`T1`–`T10`) so the PRD's traceability table can point at it. Defaults I chose without asking are marked **[default]** and can be overridden by saying so.
- **No SQL DDL and no screen descriptions appear here.** Table shapes live in `docs/BACKEND_SCHEMA.md`; screens live in `docs/APP_FLOW.md` and `docs/UI_UX.md`.

---

## 1. Architecture at a glance

Three services, one of which holds state.

```
                    ┌───────────────────────────────────────────┐
                    │  VERCEL — Hobby plan (free, no card)      │
   browser ────────▶│  web/  Next.js App Router                 │
                    │  · server components for static shells    │
                    │  · client components for anything live    │
                    │  · /api/* → rewrite to the Space  (T7)    │
                    └──────────────────┬────────────────────────┘
                                       │ HTTPS, response streamed
                    ┌──────────────────▼────────────────────────┐
                    │  HUGGING FACE SPACE — Gradio (free)       │
                    │  backend/space/  FastAPI inside Gradio   │
                    │  · one uvicorn process on port 7860      │
                    │  · all maths, all SQL, all secrets        │
                    │  · no blob storage, no queue, no Redis    │
                    └──────────────────┬────────────────────────┘
                                       │ psycopg 3, TLS, pooled
                    ┌──────────────────▼────────────────────────┐
                    │  NEON — Postgres free tier               │
                    │  aggregates, text, tokens only           │
                    │  never a row of the uploaded file        │
                    └───────────────────────────────────────────┘

   outbound from the Space only:
     · Gemini API (primary narrative)
     · OpenRouter (failover narrative)
     · api.brevo.com:443 (password reset)
     · api.github.com — never; the keep-alive runs from GitHub, not here
```

**Why this shape and not another.** Hugging Face Spaces is the only free, no-card host that gives enough RAM for pandas + scikit-learn + SHAP together. Docker Spaces require PRO, so the backend runs under the Gradio SDK with FastAPI mounted inside it: same Python process, same port, no paid plan. Vercel is the natural home for Next.js and its Hobby tier needs no payment method. Neon's free Postgres is enough because we store aggregates and text, never rows. The full comparison is in Appendix A.

**What the architecture deliberately omits.**

| Omitted | Because |
|---|---|
| Blob / object storage | The product's promise is that the file is never stored. Adding storage would break C3 rather than support it. |
| A job queue or worker process | The work takes seconds and streams in one request (T4). A queue would add a stuck-state failure mode the free host makes likely. |
| Redis or any second vendor | Postgres UPSERT counters do the job (T9). |
| A server-side PDF renderer | Print-to-PDF in the browser (PRD F7). |
| A CDN in front of the API | The Space is already behind one. |

---

## 2. Component responsibilities

| Component | Owns | Explicitly does not own |
|---|---|---|
| **Next.js (`web/`)** | Routing, layout, all rendering, form state, streamed-progress display, print stylesheet, chart drawing | Metric computation, threshold values, any copy containing a number, any secret |
| **FastAPI (`backend/`)** | Parsing, encoding, model training, metrics, bootstrap intervals, repairs, narrative generation, all persistence, all authorisation | Rendering, chart layout, deciding what a number means to the user |
| **Neon Postgres** | Accounts, sessions, analyses, metrics, narrative text, chat, share tokens, rate-limit counters, LLM cache | File rows, repaired datasets, anything that would identify an individual in the uploaded data |
| **GitHub Actions** | Lint, test, image build, keep-alive ping, deploy triggers | Holding any secret that the runtime also holds |

**The rule that keeps the split honest:** the frontend may not compute, derive, or adjust a number. Every figure it displays arrives in the payload, already rounded, with its interval and its threshold. If the UI needs a percentage, the API sends a percentage. This is what makes PRD F4-AC6 and F3-AC7 testable rather than aspirational.

---

## 3. Request lifecycle

One analysis, end to end. Each step names the decisions it exercises.

| # | Step | Where | Decisions in play |
|---|---|---|---|
| 1 | Owner picks a bundled sample or drops a file | `web/` | — |
| 2 | File posted to `POST /v1/analyses/inspect`; server parses, cleans, detects candidates, returns the confirmation card. **No rows are retained.** | Space | T2, T4 |
| 3 | Owner confirms or changes the meaning; client holds the `File` object in memory | `web/` | F2 |
| 4 | File posted **again** to `POST /v1/analyses` with the confirmations; response is a stream | browser → Vercel → Space | T4, T6, T7 |
| 5 | Server streams `stage` frames while it parses → encodes → trains 5 folds → computes metrics → bootstraps → runs SHAP | Space | T4, T5 |
| 6 | Terminal `result` frame carries the whole stored payload; client renders the verdict | both | T6 |
| 7 | Narrative generated (or served from cache) and stored with the result | Space | T9, F10 |
| 8 | Owner downloads the report (print), the JSON, or a repaired CSV | browser or Space | F6, F7 |
| 9 | Every later view is a read of the stored payload — no recomputation, no file | anywhere | T3, T9 |

**Step 2 and step 4 exist separately because of the privacy promise.** The file cannot be parked between confirm and run: parking it means storing it, and the PRD says the rows live only for the duration of a request (PRD §10, F6-AC6). So the file crosses the wire twice. That is the honest price of never keeping it, and it is invisible to the user because the browser still holds the file.

Cost of that choice, stated plainly:

- A 50 MB file is uploaded twice, so the user's effective upload is 100 MB.
- For files over 10 MB the confirmation screen says so in one line: *"This 34 MB file will be sent again when you run the analysis."*
- No server memory, no TTL, no orphan cleanup, no state to lose when the Space sleeps.

> **shortcut:** the file is re-uploaded per analysis and per repair download, so a slow link pays it repeatedly. Upgrade to a short-lived in-memory upload cache only if upload latency becomes the top complaint — it would weaken the "duration of the request" promise in PRD §10.

---

## 4. Data access layer (T2)

**Driver.** `psycopg` 3 with binary wheels, plus `psycopg_pool` for a small connection pool (`min_size=1`, `max_size=4`). One process, one pool. The Space's free tier gives 2 vCPU; four connections is already more than we can use.

**No ORM, no query builder.** Every statement is either a named `.sql` file under `backend/app/db/queries/` or a literal query inside a repository function. Parameters are always `%s` placeholders. Identifiers are never interpolated from user input — where a column name must reach SQL (dynamic `ORDER BY`, pivot on a group label), it passes through an allow-list built from the file's own parsed header list.

**Migrations.** Numbered files, applied in lexical order.

```
backend/app/db/migrations/
  0001_accounts.sql
  0002_sessions.sql
  0003_analyses.sql
  0004_shares.sql
  0005_limits_cache.sql
  ...
```

| Rule | Detail |
|---|---|
| Table of record | `schema_migrations(version text primary key, checksum text not null, applied_at timestamptz not null default now())` |
| Application | One transaction per file: the DDL and the `schema_migrations` insert commit together, so a half-applied migration is impossible |
| Concurrency | The runner takes `SELECT pg_advisory_lock(4823017)` before reading state and releases it after, so two container starts cannot race |
| Checksums | A changed checksum on an already-applied file is a startup failure, not a warning. Editing history is how databases drift. |
| Down-migrations | **None.** Rollback is a Neon branch restore. Stated here so it reads as a decision, not an oversight. |
| When it runs | In the container entrypoint, before uvicorn binds the port. A failed migration means the app never accepts traffic. |

The runner is about thirty lines: connect, lock, `CREATE TABLE IF NOT EXISTS schema_migrations`, read applied versions, sort the directory, apply the missing ones, unlock. Deliberately boring.

**Transactions.** One per unit of work, opened with `with conn.transaction():`. A partial write is never left behind — the analysis row and its metric rows are one transaction, and so are the account deletion cascades.

**Endpoints are synchronous `def`, not `async def`.** FastAPI runs them in its threadpool, which is exactly right for CPU-bound pandas work and blocking psycopg. Mixing async defs with a blocking driver would tie up the event loop and produce a mystery: every request slower than the last. Threadpool capped at 8 workers. Uvicorn runs **one** worker process, because two would halve the memory available to SHAP and complicate the analysis semaphore in §6.

---

## 5. Authentication and sessions (T3)

### 5.1 Sessions

| Property | Value |
|---|---|
| Token | `secrets.token_urlsafe(32)` — 256 bits, 43 characters |
| Storage | SHA-256 hex digest only. The raw token exists in the cookie and nowhere else |
| Lookup | Indexed read on `token_hash`; constant-time comparison is unnecessary because we look up by hash, not compare |
| Cookie | `fl_session`; `HttpOnly`; `Secure`; `SameSite=Lax`; `Path=/`; no `Domain`; 30-day `Max-Age` **[default]** |
| Creation | New token on every successful login, so a fixed session cannot survive an authentication |
| Revocation | `DELETE FROM sessions WHERE token_hash = %s`, immediate, no denylist |
| Global revocation | Password change deletes every row for that user. Account deletion removes them via the foreign key |
| Expiry sweep | `DELETE FROM sessions WHERE expires_at < now()` — run at container start and on each login. No cron, no scheduler |
| Absolute vs idle | Absolute 30 days, no idle timeout. A reporting tool is used in bursts; an idle timeout would just annoy the owner |

Why this rather than a JWT: the PRD requires instant revocation three separate times — F7-AC2 (share links), F8-AC2 (password reset), F9-AC1 (account deletion). A stateless token needs a revocation table anyway, so a stateless token here is a denylist with extra steps.

### 5.2 Google sign-in

Authorisation-code flow with PKCE, implemented by hand against Google's endpoints — no heavyweight auth library for two redirects.

- Scopes: `openid email profile` only. Nothing that needs Google verification.
- `state` and `code_verifier` live in short-lived `HttpOnly` cookies, single use.
- No access token, refresh token or `id_token` is retained after the callback. We read `sub`, `email`, `email_verified` and the display name, then forget everything else. There is no offline access, so Google's 7-day refresh-token expiry for unverified apps is irrelevant.
- Consent screen is published to **In Production**. In Testing mode the 100-user cap and the "unverified app" warning would both appear in a demo.
- A privacy page reachable without login is required by Google's branding rules and is part of the build, not an afterthought.

### 5.3 Password accounts

| Property | Value |
|---|---|
| Hash | **argon2id** via `argon2-cffi`; parameters `time_cost=3, memory_cost=65536, parallelism=1` **[default]** |
| Fallback | bcrypt (cost 12) if argon2 wheels fail to install on the host — decided at import time, recorded in the log |
| Minimum length | 8 characters, plus at least one capital letter, one number and one special character; maximum 128 |
| Not enforced | A common-password blocklist. Length plus argon2 plus the login rate limit in §10 is the better trade; adding a wordlist is a later upgrade |
| Comparison | Always performed, even for unknown accounts, against a dummy hash, so response timing does not leak account existence |

### 5.4 Password reset over Brevo's HTTPS API

- Request: `POST /v1/auth/reset/request` with an email. Always returns the same generic `202`, whether or not the address exists (F8-AC3).
- Token: `secrets.token_urlsafe(32)`, SHA-256 stored, **30-minute expiry**, `used_at` set on consumption, invalidated wholesale by a password change (compared against `users.password_changed_at`).
- Sending: one HTTPS `POST https://api.brevo.com/v3/smtp/email` with the API key in the header, 20-second timeout, one message per request. **No SMTP anywhere** — Spaces block every port except 80, 443 and 8080, so a mail client on port 587 can never work there.
- Failure policy: log the exception **without the address**, return the same generic success. Never leak failure to the requester.
- Volume: Brevo's free plan is 300 emails per day and needs no card. The 3-per-hour-per-address limit in §10 sits well under it.
- Startup check: if `BREVO_API_KEY`/`BREVO_SENDER` are missing in a production environment, **the app refuses to start** (F8-AC6). Failing at the first reset request, silently, is worse.
- Known cost: the free plan adds a "Sent with Brevo" footer and only sends from a verified sender address. Both are acceptable for a portfolio app and stated in the README.

### 5.5 Share links

- Token `secrets.token_urlsafe(32)`, SHA-256 stored, no expiry by default (PRD F7).
- Revocation is a `DELETE`; the next request for that token returns `404`, not `403` — an attacker learns nothing about whether it ever existed.
- The share lookup path can only ever load the stored analysis payload. There is no code path from a share token to row data, because row data does not exist anywhere.

---

## 6. Analysis pipeline (T5)

### 6.1 Stages and budget

Budget is **55 seconds** wall clock, chosen to expire before any proxy in the chain gives up. When it is exceeded the run terminates with a `analysis_budget_exceeded` problem whose `detail` tells the user to sample the file.

| # | Stage | Frame name | Soft deadline | What happens |
|---|---|---|---|---|
| 1 | Read and parse | `parsing` | 8 s | Delimiter/encoding detection, XLSX sheet read, size and shape guards |
| 2 | Clean and encode | `cleaning` | 10 s | Drop empty columns and exact duplicates, fill blanks, band age, encode categoricals, choose the positive label |
| 3 | Train | `training` | 25 s | 5-fold stratified CV, one logistic regression per fold, out-of-fold predictions assembled |
| 4 | Measure | `measuring` | 35 s | C1–C5, per-group table, 1,000-resample bootstrap, association/proxy scan |
| 5 | Influence | `influence` | 45 s | SHAP mean-absolute on at most 500 sampled rows; failure is non-fatal |
| 6 | Save | `saving` | 52 s | One transaction: analysis row, metric rows, thresholds, model card |
| 7 | Narration | — | 55 s | Served from cache if present; otherwise requested and stored. Template if providers fail |

Deficiencies are non-fatal by design: a slow SHAP run marks the technical view's influence section unavailable (F3-AC5) rather than failing the analysis, and a failed LLM call falls through to the template (F4-AC4).

### 6.2 Determinism

Same file plus same confirmations must produce byte-identical numbers (F3-AC1). The mechanism:

```
seed = int.from_bytes(sha256(file_bytes + canonical_json(confirmations)).digest()[:4], "big")
```

That seed drives the fold splitter, the bootstrap resampler and the SHAP row sample. No `random`, no clock, no environment-dependent ordering — group labels are sorted, the fold splitter is given a fixed seed, and the bootstrap uses a `numpy.random.Generator(PCG64(seed))`.

The model card stores `engine_version` (a constant bumped whenever the maths changes), so a golden test failure can distinguish "we broke the maths" from "we intentionally changed it".

### 6.3 The model

| Property | Choice | Why |
|---|---|---|
| Algorithm | `LogisticRegression(max_iter=1000)` | Interpretable, fast on 50k rows, and its coefficients give the reviewer a sanity check against SHAP |
| Preprocessing | One-hot for categoricals (`handle_unknown="ignore"`), standard scaling for numerics | Deterministic, no leakage; fitted inside each fold |
| Sensitive column | **Kept as a feature** | The question is what this data teaches a model, not what a model learns with demographics removed (PRD F3) |
| Validation | `StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)` | Every reported model metric comes from a row the model never saw (F3-AC2) |
| Reported accuracy | Out-of-fold only | v1's in-sample accuracy was the single most misleading number it produced |

### 6.4 Metrics and intervals

| Quantity | Implementation | Notes |
|---|---|---|
| Selection rate per group | `fairlearn.metrics.selection_rate` | Historical, and model (from OOF predictions) |
| Parity ratio / difference | Derived from selection rates | Ratio for the check, difference for the amplification comparison |
| Equal opportunity | `fairlearn.metrics.equalized_odds_difference`-family, TPR gap computed explicitly per group | Reported as `max(TPR) − min(TPR)` |
| Confidence intervals | **Written here:** 1,000 resamples of rows with replacement, recompute per-group rates and the ratio, take the 2.5th and 97.5th percentiles | About forty lines of numpy. Bootstrap libraries pull in more than they save, and this one is worth owning |
| Inconclusive triggers | Per PRD §8.4: any group < 30 rows, CI half-width > 0.10, no positives, no negatives | Reasons are enumerated strings, not prose, so the UI can translate them. A one-group demographic is refused at confirmation, not reported as Inconclusive |
| Feature influence | `shap.LinearExplainer` on the OOF-trained fold-agnostic model, mean absolute value, top 15 features | Sampled to 500 rows for speed |
| Proxy detection | Cramér's V for categorical pairs, absolute point-biserial for numeric | Top three by association with the sensitive column become the default flagged correlates in F6 |

Bootstrap and SHAP both run only when the row counts make them meaningful; a check already flagged Inconclusive for `Group too small` skips its resampling rather than producing a number nobody should read.

### 6.5 Memory and concurrency

Ceiling to be proven at gate G9: the largest accepted file, 50,000 rows × 60 columns, mixed types.

| Step | Approximate peak |
|---|---|
| pandas frame, parsed | 300–600 MB (object dtype dominates) |
| One-hot expansion (capped at 200 total columns; rare categories grouped) | ×2–3 |
| Logistic regression × 5 folds | a few hundred MB |
| SHAP on 500 rows | under 100 MB |
| **Realistic peak** | **~1.5–2.5 GB** |

Against 16 GB that is comfortable, but the guard matters because two concurrent 50k analyses plus a cold SHAP run is how a free host dies. An `asyncio`/threading **semaphore of 2** concurrent analyses per process; the third request is not queued indefinitely — it returns `429 rate_limited` with `Retry-After: 10`. One worker process means the semaphore is the true global limit.

One-hot expansion cap: columns with more than 30 distinct values are grouped into `other` for all but the 30 most frequent. Without this a high-cardinality ID column silently explodes the matrix.

### 6.6 Repairs

Three strategies, all evaluated under the **same fold assignment and seed** as the original (F6-AC2), so the comparison is like-for-like.

| Strategy | Mechanism | Output shape |
|---|---|---|
| Reweigh | `instance_weight = P(group)·P(outcome) / P(group, outcome)` per cell | Same rows, one extra column |
| Resample | Duplicate or drop rows to reach the expected cell counts under independence; hard cap at 3× the input rows | Same columns, different row count |
| Drop and re-check | Remove the sensitive column plus user-selected flagged correlates, then retrain | Fewer columns |

Every strategy is regenerated on demand from the re-uploaded file, never stored. Because the pipeline is deterministic, regenerating for a download produces the same bytes that were measured — which is what makes F6-AC7 (same hash twice) true rather than hopeful.

---

## 7. Streaming contract (T4)

### 7.1 Why not SSE, and why not a job table

`EventSource` can only issue GET requests and cannot carry a file, so it is unusable here. That leaves us free to pick a simpler wire format than SSE's framing: **newline-delimited JSON over a normal `fetch` response body**, `Content-Type: application/x-ndjson`. Each line is one complete JSON object, which means the client parser is a string split and a `JSON.parse` — no event-type/reconnection machinery to implement, because we are not implementing reconnection.

No job table, no status column, no worker. The work happens inside the request that the user is waiting on, so a host restart cannot strand anything. The cost is that a page refresh cancels the run — acceptable for a ten-second operation, and the alternative (resumable jobs) is a bigger product than this one.

### 7.2 Frames

```jsonc
{"event":"stage","stage":"parsing","index":1,"total":6,"label":"Reading your file"}
{"event":"stage","stage":"training","index":3,"total":6,"label":"Training the stand-in model"}
{"event":"ping"}                                  // every 5s if a stage is slow
{"event":"result","payload":{ /* the stored analysis object */ }}
{"event":"error","problem":{ /* RFC 9457, identical to any JSON error body */ }}
```

Rules the client can rely on:

1. Frames arrive in order.
2. **Exactly one terminal frame** — `result` or `error` — and nothing follows it.
3. An unknown `event` is ignored, not thrown. This is how a server-side addition ships without a coordinated frontend release.
4. `stage` frames are advisory. The client must render a complete verdict from `result` alone, so no state lives in the progress list.

### 7.3 Errors after HTTP 200

Once the first frame is flushed the status code is fixed, so a failure discovered at stage 4 cannot be a 500. It is a terminal `error` frame carrying the **same problem object** used for ordinary responses. One error schema, two delivery paths — the frontend has one error component, not two.

Client obligation: if the stream ends without a terminal frame, treat it as `internal_error` and offer a retry. A dead socket must not look like a slow analysis forever.

### 7.4 The proxy question, settled by measurement

Vercel's rewrite proxies the request to the Space. Whether it forwards a chunked response without buffering it until completion determines whether the progress list is real or theatre.

- **Day-one gate (Gate G1 in §15):** deploy a throwaway endpoint that emits three frames 500 ms apart and `curl -N` it through the rewritten path. Watch whether frames arrive spaced or all at once.
- **If buffered:** the Space has a server-side switch, `STREAMING_ENABLED=0`, that returns one JSON body instead of NDJSON. The client branch for that body is not built, so the fallback today is a code change, not a flag. **The verdict is unaffected** - only the progress display is lost.
- **Rejected fallback:** calling the Space directly from the browser. It would need `SameSite=None` cookies, which Safari and Firefox block by default; hiring a whole auth complication to keep a progress bar is a bad trade.

One flag, one code path, decided by a human on day one rather than discovered by a user.

---

## 8. HTTP API (T6)

### 8.1 Shape

Resource-oriented, versioned, under `/v1`. FastAPI generates OpenAPI 3.1 at `/docs` and `/openapi.json`; that document is the contract the frontend client is generated from (§9.3).

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/v1/health` | none | Liveness plus a `SELECT 1` so the keep-alive warms Neon too |
| `GET` | `/v1/health/stream` | none | Three spaced frames — the G1 proxy probe |
| `GET` | `/v1/samples` | none | The three bundled datasets and what each demonstrates |
| `POST` | `/v1/analyses/inspect` | none¹ | Multipart file → cleaned shape, detected card, warnings. Retains nothing |
| `POST` | `/v1/analyses` | none¹ | Multipart file + confirmations → **NDJSON stream** |
| `GET` | `/v1/analyses` | user | History, paginated |
| `GET` | `/v1/analyses/{id}` | user, share, or ephemeral run id | Stored payload, or the in-process payload for an anonymous sample run |
| `DELETE` | `/v1/analyses/{id}` | user | Deletes the analysis, its metrics, narrative, chat and shares |
| `POST` | `/v1/analyses/{id}/repairs` | user or ephemeral run id | Multipart file + confirmations, or no file for a sample → comparison of all three strategies (JSON) |
| `POST` | `/v1/analyses/{id}/repairs/{strategy}/dataset` | user or ephemeral run id | Multipart file + confirmations, or no file for a sample → repaired CSV stream |
| `POST` | `/v1/analyses/{id}/chat` | user or share | One grounded question → one answer. An owner's turn is stored; a share viewer's is not |
| `POST` | `/v1/analyses/{id}/shares` | user | Create a share token |
| `DELETE` | `/v1/shares/{token}` | user | Revoke |
| `GET` | `/v1/shared/{token}` | token | Read-only report payload, aggregates only |
| `POST` | `/v1/auth/signup` | none | Email + password |
| `POST` | `/v1/auth/login` | none | Email + password |
| `POST` | `/v1/auth/logout` | user | Deletes the session row |
| `GET` | `/v1/auth/google/start` | none | 302 to Google with PKCE |
| `GET` | `/v1/auth/google/callback` | none | 302 back, sets the cookie |
| `POST` | `/v1/auth/reset/request` | none | Generic 202, always |
| `POST` | `/v1/auth/reset/confirm` | none | Token + new password |
| `GET` | `/v1/me` | user | Identity, for the header |

¹ Sample runs need no account. An anonymous sample run writes nothing: its result lives in a short-lived in-process cache keyed by the run id and expires within 30 minutes or on restart. A signed-in sample run is stored like any other analysis. Own file uploads require a session (PRD Q10, the half wall). The endpoint returns `401` for an anonymous upload rather than silently degrading, so the UI can prompt sign-in precisely.

**Why repair downloads take the file again:** the repaired CSV is rebuilt from the original rows, which we no longer have. Re-uploading is the cost of the no-retention promise, and it is deterministic, so the file the user receives is the one that was measured. A bundled sample is the one exception: the server already has that CSV by `sample_slug`, so no upload is requested and the no-retention promise is untouched.

### 8.2 Errors — RFC 9457

Every failure, in a response body or a terminal stream frame, is the same object:

```json
{
  "type": "urn:fairlens:error:rate_limited",
  "title": "Too many analyses",
  "status": 429,
  "detail": "You have run 5 analyses in the last hour. Try again in 12 minutes.",
  "instance": "/v1/analyses",
  "code": "rate_limited",
  "retry_after": 720,
  "fields": []
}
```

`type` uses a `urn:fairlens:error:*` identifier rather than an `https://` URL, because there is no public site to host the documentation at and a dead link is worse than an opaque-but-honest URN.

| `type` suffix | Status | When |
|---|---|---|
| `validation_error` | 422 | Shape or type problem; `fields` names the offending inputs |
| `unsupported_file` | 415 | Not CSV/XLSX, or not tabular |
| `file_too_large` | 413 | Over 50 MB, detected from `Content-Length` before reading |
| `too_many_rows` | 422 | Over 100,000 rows after parsing |
| `too_few_rows` | 422 | Under 50 rows or under 2 usable columns |
| `ambiguous_confirmation` | 422 | Outcome and demographic the same column, single-value column, zero-row positive cell |
| `analysis_budget_exceeded` | 504 | The 55-second budget elapsed |
| `unauthenticated` | 401 | No valid session |
| `invalid_credentials` | 401 | Wrong password, or unknown email — indistinguishable |
| `forbidden` | 403 | A resource belonging to another user |
| `not_found` | 404 | Including revoked share tokens |
| `rate_limited` | 429 | With `retry_after` |
| `conflict` | 409 | Duplicate email at signup |
| `provider_unavailable` | 503 | Both LLM providers failed and the template is being used — emitted as a warning field, not a hard failure |
| `internal_error` | 500 | Anything unhandled |

`detail` is written for the user reading it, in the PRD's voice. No stack traces, no exception class names, no SQL (PRD F1-AC6). The correlation id is in a header, not in `detail`.

### 8.3 Versioning policy

`/v1` is **additive only**. New fields, new endpoints and new optional request keys are allowed. Removing a field, renaming one, changing a type or changing a default behaviour requires `/v2`, and `/v1` is deleted the day `/v2` ships — there is one consumer, so a deprecation window would be ceremony.

---

## 9. Frontend architecture (T7, T8)

### 9.1 The same-origin proxy, and why it is not optional

`next.config.mjs` rewrites `/api/:path*` to `${API_ORIGIN}/:path*`. The browser therefore only ever sees one origin:

- Cookies are **first-party**, so `SameSite=Lax` works and Safari/Firefox third-party cookie blocking never applies.
- No CORS preflight, no `Access-Control-Allow-Credentials`, no origin allow-list.
- No CSRF token. The combination of `SameSite=Lax`, a same-origin-only client, and no state-changing `GET` closes the class; a token would be a fourth mechanism guarding a door that is already shut.

A full cross-origin design would require `SameSite=None` — which those browsers block by default — making login silently fail for a subset of users. That is the single strongest argument for the proxy.

**One open question against this decision:** how large a request body the proxy will carry. Vercel documents a 4.5 MB limit for Functions; a rewrite should be handled by the edge proxy instead, but the PRD asks for 50 MB uploads. Gate G3 in §15 measures it on day one, and the fallback is direct-to-Space uploads authenticated by a one-time ticket rather than a cookie — which keeps the third-party cookie problem out even in the fallback.

### 9.2 Routes

```
web/app/
  page.tsx                      landing: the three samples + upload dropzone
  analysis/[id]/page.tsx        summary + collapsed technical view + repairs section
  shared/[token]/page.tsx       read-only report
  history/page.tsx
  account/page.tsx              password change, appearance, delete account
  login/ signup/ reset/ reset/confirm/   auth
  privacy/page.tsx
```

- **Server components** render the shell, layout, static copy and the landing page. No secret ever reaches a client component; the API origin is used only by the rewrite.
- **Client components** own anything live: the dropzone, the confirmation card, the stream reader, the charts, the chat, the repair table.
- **Authed data is fetched client-side** with `credentials: "include"` against `/api/v1/...`. Server-side fetching would put the session cookie on the Vercel side of the proxy for no benefit, and would defeat the streaming path.

### 9.3 The generated client is the contract test

`openapi-typescript` generates `web/lib/api-types.ts` from the committed `backend/openapi.json`.

- CI regenerates and runs `git diff --exit-code`. A backend change that is not reflected in the committed schema fails the build — which is exactly the drift the PRD's traceability claim depends on.
- The fetch wrapper is about sixty lines around `fetch`: base path, JSON encoding, problem+json parsing into one `ApiError` class, and `credentials: "include"`.
- No React Query, no SWR **[default]**. There are six fetches in this app and one stream; a caching library would add a state model bigger than the app's. Plain `useEffect` plus a small `useAnalysisStream` hook.

### 9.4 Streaming reader

```ts
const res = await fetch("/api/v1/analyses", { method: "POST", body: form });
const reader = res.body!.getReader();
const decoder = new TextDecoder();
let buf = "";
for (;;) {
  const { done, value } = await reader.read();
  if (done) break;
  buf += decoder.decode(value, { stream: true });
  let i;
  while ((i = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, i); buf = buf.slice(i + 1);
    if (line.trim()) handleFrame(JSON.parse(line));
  }
}
```

Plus: `AbortController` on unmount (a navigation cancels the run, as §7.1 says), and the "ended without terminal frame" rule from §7.3.

### 9.5 Charts (T8)

Recharts, three charts, no chart library beyond it:

| Chart | Type | Note |
|---|---|---|
| Selection rate by group | Grouped bar, historical vs model | The one Maya screenshots |
| Gap with interval | Custom error-bar shape | ~20 lines; Recharts has no whisker primitive and does not need one |
| Feature influence | Horizontal bar, top 10 | Technical view only |

Accessibility is enforced, not intended: every chart ships a text alternative and a data table behind a disclosure, because a canvas of bars is invisible to a screen reader and PRD F4 forbids hiding a number.

### 9.6 Component system

Tailwind plus shadcn/ui, whose components are **copied into the repo** and built on Radix. We own the code, Radix owns focus management, keyboard behaviour and ARIA. Dialogs, selects, tooltips and tables are all cases where a hand-rolled version is worse, and a week of work nobody budgeted.

Colour is never the only signal on a verdict — icon, text label and colour together (PRD F4, and a hard accessibility requirement).

---

## 10. Limits, cache and shared counters (T9)

### 10.1 Rate limits

One table, one statement, atomic under concurrency:

```sql
INSERT INTO rate_limits (bucket, identifier, window_start, count)
VALUES (%s, %s, date_trunc('hour', now()), 1)
ON CONFLICT (bucket, identifier, window_start)
DO UPDATE SET count = rate_limits.count + 1
RETURNING count;
```

| Bucket | Identifier | Limit | PRD |
|---|---|---|---|
| `anon_analysis` | peppered SHA-256 of the client IP (BACKEND_SCHEMA S5) | 5 / hour | F12-AC1 |
| `user_analysis` | user id | 20 / hour | F12 |
| `ai_call` | user id | 60 / hour | F12 (separate from analyses so chat cannot starve narratives) |
| `reset_email` | email (hashed) | 3 / hour | F8 |
| `login_fail` | IP + email hash | 10 / hour | §11 |

Rules:

- Counting happens **before** any work, so a rejected request stores nothing (F12-AC3).
- Over the limit returns `429` with `Retry-After` computed from the window end — never a 500.
- The limit for anonymous requests is also applied to authenticated ones when the IP bucket is already exhausted, so an account is not a free bypass for a script.
- Old windows are swept on startup and on login, alongside the session sweep. No cron.
- `X-Forwarded-For` is read from the first hop only, because the Space sits behind a proxy. A spoofed header can therefore only change a bucket the attacker already controls.

### 10.2 LLM cache

```sql
CREATE TABLE llm_cache (
  key_hash       text primary key,
  analysis_id    uuid references analyses(id) on delete cascade,
  kind           text not null,          -- 'narrative' | 'chat'
  prompt_version text not null,
  response       jsonb not null,
  created_at     timestamptz not null default now()
);
```

- Key: `sha256(analysis_id ‖ kind ‖ normalised_question ‖ provider ‖ prompt_version)`.
- Re-opening a stored report makes **zero** model calls (F10-AC6) — the narrative is read from `analysis_narratives`, and the cache exists to stop the same question being paid for twice.
- Deleting an analysis deletes its cache rows through the foreign key. Nothing is retained that could quote a deleted report.
- `prompt_version` in the key means editing a prompt misses old cache entries automatically, with no manual flush. A stored report keeps its narrative; the new prompt applies to analyses run after the change.

---

## 11. Security posture

### 11.1 Response headers **[default]**

| Header | Value |
|---|---|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `X-Frame-Options` | `DENY` (with `frame-ancestors 'none'` in CSP) |
| `Content-Security-Policy` | `default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` |

`style-src 'unsafe-inline'` is required because Radix writes inline styles. Stated rather than hidden; the alternative is a nonce pipeline for no measurable gain on this app.

**`script-src 'self'` needs no exception for the theme.** The theme preference is stored in a cookie and resolved while the page is rendered (`data-theme` on `<html>`, or a `prefers-color-scheme` media query when the preference is "system"), so there is no inline pre-paint script. If a future change introduces one to avoid a flash, it must be hashed or nonced rather than loosening `script-src` — recorded here so that shortcut is not taken by accident.

### 11.2 Upload guard order

Order matters — every check that can happen without reading the body, does.

1. `Content-Length` missing → `411`.
2. `Content-Length` > 50 MB → `413`, body never read (F12-AC4).
3. Streamed read capped at 50 MB regardless of the header — a lying header cannot cause a buffer blow-up.
4. Extension and magic-byte sniff → CSV, XLSX or `415`.
5. Row and column caps after parsing → `422` with the specific limit named.
6. Parse failure → `unsupported_file` with a human sentence, never an exception string.

Parsing runs with `openpyxl(read_only=True)` and pandas `chunksize` where a full frame is not needed, so a malformed 50 MB file cannot exhaust memory before it is rejected.

### 11.3 Logging **[default]**

- One JSON object per line to stdout, collected by the host.
- Fields: `ts`, `level`, `request_id`, `method`, `path`, `status`, `duration_ms`, `user_id`, `event`.
- **Never logged:** passwords, tokens (session, reset, share), API keys, email addresses (a peppered hash is used instead), column values, group labels, row data, request bodies.
- A `redact` filter runs on the way out with an explicit key list, so a careless `logger.info(extra=payload)` cannot leak. A test asserts that a request containing an email address produces no log line containing it (F8-AC4).
- The correlation id is echoed in `X-Request-Id` so a user report can be matched to a log line without either containing their data.

### 11.4 Secrets **[default]**

- Environment only. `.env.example` is committed with names and no values; `.env` is git-ignored.
- Loaded through a settings model at startup with an explicit required set, validated before the port binds. Missing secrets produce a startup failure naming the **variable names**, never the values.
- Space secrets for the backend, Vercel environment variables for the web app. The only value the web app holds is `API_ORIGIN` — deliberately, so no LLM key or Brevo key can leak into a client bundle.

### 11.5 Prompt-injection boundary

Uploaded column headers, group labels and cell values are untrusted text that reaches an LLM. Mitigations: user-derived text is wrapped in explicit delimiters, the system prompt states that content inside delimiters is data and never instructions, and every generated number is substituted after generation with any invented digit rejecting the response (PRD F10-AC1). The narratives are also stored, so what a reviewer reads is what the server accepted.

---

## 12. Deployment and environments

### 12.1 Backend runtime (Gradio Space)

```python
# backend/space/app.py
app = FastAPI()
...
uvicorn.run(gr.mount_gradio_app(app, gradio_page, path="/"), host="0.0.0.0", port=7860)
```

- The Space runs `app.py` under the **Gradio SDK** on the free ZeroGPU allowance. Gradio exists only to satisfy the SDK; the product talks to FastAPI. Docker Spaces need PRO, which C1 forbids.
- `requirements.txt` is pinned in `backend/space/`. An unpinned ML stack is a cold-start and reproducibility hazard.
- One process, one uvicorn worker on port `7860`, which is what Spaces expects. That keeps memory predictable and makes the analysis semaphore the real global limit.
- **Free-tier consequence:** a Space built from a free account is a **public repository**. The code is visible; secrets are not. For a portfolio project this is acceptable and said out loud.
- The host's CPU share is small. G9 measures it before any feature is built; the fallbacks are in §15.

Local development still uses the image below, in `docker-compose.yml`:

```dockerfile
FROM python:3.12-slim
# non-root user, uv for a frozen, hashed install
ENTRYPOINT ["/app/entrypoint.sh"]   # migrate under advisory lock, then exec uvicorn
```

- `uv sync --frozen` from the committed lock file. `python:3.12-slim`, not alpine — wheels for numpy/scipy/shap are manylinux and alpine would force source builds measured in minutes.
- The entrypoint runs the migration step and only then `exec uvicorn app.main:app --workers 1`.

### 12.2 Frontend

Vercel Hobby, root directory `web/`, one environment variable. Preview deployments per pull request (T10).

Previews call the **same** production API and Neon database. That is stated rather than solved with a second backend, because there is no real user data to protect and a second Space plus a second Neon branch would double the moving parts for a portfolio app.

### 12.3 Keep-alive

A GitHub Actions schedule hits `/v1/health` every 14 minutes on the public repo. The endpoint also runs `SELECT 1`, so one ping keeps both the Space and Neon warm.

Two honest caveats: GitHub disables scheduled workflows on repos with no activity for 60 days, and the first request after any sleep may still take 30–60 s. The PRD's S2 metric is therefore measured **warm**, and the docs say so.

### 12.4 Environments **[default]**

| Environment | Backend | Database | Purpose |
|---|---|---|---|
| Local | `docker compose` | container | Development, tests |
| Preview | The production Space | Production Neon | Per-PR UI review |
| Production | The production Space | Production Neon | The demo |

There is no separate staging tier: on a free plan, a staging environment would be a fourth thing to keep alive and would be stale within a week.

---

## 13. Testing and delivery (T10)

### 13.1 Layers

| Layer | What it proves | Tooling |
|---|---|---|
| **Unit** | Fairness maths against hand-computed fixtures; encoding; delimiter/encoding detection; age banding; the bootstrap's interval on a known distribution | pytest, no database |
| **Golden** | The three bundled samples produce their documented verdicts and parity ratios, end to end, through the real pipeline | pytest |
| **Integration** | Raw SQL is correct: migrations apply, cascading deletes leave zero rows, the UPSERT counter is atomic under concurrency | pytest against a **real Postgres service container** — never SQLite, whose dialect would test nothing we ship |
| **Contract** | The committed `openapi.json` matches the app, and the generated client compiles against it | a generation step plus `git diff --exit-code` |
| **Image** | The Docker image builds, boots, migrates and analyses one sample | GitHub Actions |
| **End-to-end** | The demo path works in a browser: sample → verdict → repair → download | Playwright |
| **Accessibility** | No critical axe violations on the four verdict states and the login page | `@axe-core/playwright` |
| **Log hygiene** | No email, token or row value reaches the log | pytest, grepping captured output |

### 13.2 Build order — skeleton first

The pipeline is not built in one go. Each milestone ends with something that runs.

| # | Milestone | Exit check |
|---|---|---|
| **M0** | Walking skeleton: Space boots, `/v1/health` answers, Next page renders, **one bundled sample analysed end to end**, one golden test. No database: the result lives in the response and an in-process cache | The demo exists and is deployed |
| **M1** | Database: migrations, accounts/sessions/analyses tables, golden tests in CI against a Postgres container | `docker compose up` gives a working stack, and the ten-zero deletion test passes |
| **M2** | Auth plus upload: signup, login, Google, logout, sessions, the `/v1/me` guard; file guards, the confirmation card, the six-stage log | An anonymous upload returns 401, a signed-in one succeeds |
| **M3** | The full verdict UI: five checks, four states, chart, technical view | Summary numbers all traceable to the payload |
| **M4** | Repairs: three strategies, comparison table, CSV downloads | Same hash on a re-run |
| **M5** | Report, share links, print, history, account | A revoked token 404s immediately |
| **M6** | Narrative and chat with template fallback | Zero LLM calls on re-open |
| **M7** | Pipeline completion: contract tests, image tests, axe, previews | Every layer in §13.1 is green; G1–G4 and G9 have recorded outcomes |
| **M8** | Hardening: rate limits, privacy page, keep-alive, startup secrets, sweeps | Rate limits hold under a concurrent probe and the keep-alive has stayed green for 24 hours |

Every milestone lands its own tests in the same change; M7 verifies rather than writes. The per-milestone file lists, exit commands and cut-line items are in `docs/IMPLEMENTATION_PLAN.md` §4.

The reason for this order, stated once: four days of CI configuration on an app that does not run yet is how a project stalls — and Gate G1 (does Vercel pass the stream through?) is measured on day one, before a progress design is built on top of it.

### 13.3 CI

- **On pull request:** lint (ruff, eslint), type check (mypy, tsc), unit + golden + integration + contract tests, Playwright smoke against a compose stack, axe assertions. Preview deployment for visual review.
- **On merge to main:** the same suite, then the Space rebuilds from the repository.
- Migrations are never applied by CI against production; the container applies them at start, under the advisory lock.

---

## 14. Local development **[default]**

```
docker compose up          # postgres + api + web, migrations at boot
```

| Service | Port | Notes |
|---|---|---|
| `db` | 5432 | `postgres:16`, named volume, seeded with the three samples' expected results |
| `api` | 7860 | Bind mount, uvicorn `--reload`, entrypoint runs migrations |
| `web` | 3000 | npm dev server, `API_ORIGIN=http://localhost:7860` |

- `.env.example` documents every variable, with the Brevo and LLM values blank so the app starts in template-fallback mode out of the box (PRD C5 - the product must work with no key).
- A `scripts/seed.py` inserts a demo account and one sample analysis so the history and share pages are inspectable without clicking through.
- Commands are written for PowerShell as well as bash: no `make`, no shell-only `export`, no symlinks. The primary development machine is Windows.

---

## 15. Risks and verification gates

Five of these are cheap now and expensive later. Each has a check and a written fallback.

| # | Risk | Gate | Fallback |
|---|---|---|---|
| **G1** | Vercel's rewrite buffers the streamed response, so progress frames arrive all at once at the end | **Day 1** — `curl -N` the three-frame probe through the deployed rewrite | Measured unbuffered on 2026-11-15. If it regresses, `STREAMING_ENABLED=0` returns one body; the client branch for it is not built |
| **G2** | Spaces reach only ports 80, 443 and 8080, so password reset cannot send over SMTP | **Day 1** — one real send through Brevo's HTTPS API from the running Space | None needed: Brevo is the design. If the sender address is rejected, verify it in Brevo; the app still starts and logs the failure (F8-AC6) |
| **G3** | **The most likely thing to break the PRD's 50 MB cap.** Vercel documents a 4.5 MB request-body limit for *Functions*. A rewrite to an external host is routed by the edge proxy rather than by a function, so it should not inherit that limit - but this must be measured, not assumed | **Day 1** — post a 60 MB file through the rewrite and check bytes received at the Space | If the proxy refuses bodies over 4.5 MB: uploads go **direct to the Space** with a one-time ticket (`POST /v1/uploads/ticket` returns a nonce bound to the session, the browser then posts the file to the Space with the nonce in a header instead of a cookie - which sidesteps third-party cookie blocking). Non-streaming routes stay proxied. Real work, not a config change, which is why the gate is day one and not M4 |
| **G4** | SHAP or fairlearn fails to install or import on the Space's Python | **Day 1** — the Space build, then `/v1/health` reports both versions | Pin Python 3.11 in the Space; if SHAP still fails, influence degrades (F3-AC5) and the verdict is unaffected |
| **G5** | Neon free tier's 0.5 GB is exceeded | ongoing | Aggregates only: one analysis is roughly 20–40 KB of JSON, so ~15,000 analyses. Not a near-term risk |
| **G6** | The GitHub keep-alive cron is disabled after 60 days of repository inactivity | ongoing | Accept one 30–60 s cold start, or move the ping to another free scheduler |
| **G7** | Google's consent screen cannot be published to In Production without verification, leaving the 100-user cap and the warning screen | **M2** | Basic scopes normally avoid verification; if not, the cap is irrelevant at portfolio scale and the warning is a demo blemish |
| **G8** | Brevo's free plan changes, or the verified sender lapses | Reset mail stops; new accounts unaffected | Verify the sender once; the app starts and logs the failure (PRD R1) |
| **G9** | The heaviest pipeline operations exceed the 20-second warm target or the 55-second budget on the free host, because install success is not speed | **Day 1** — a synthetic 50,000 × 60 benchmark on the deployed Space: parse, 5-fold logistic regression, 1,000 bootstrap resamples, SHAP on 500 rows. Cold and warm recorded | Reduce the SHAP sample to 200 rows. If still over, the sampling offer becomes mandatory at 25,000 rows — a PRD change, recorded rather than silently applied |

Each gate is a checklist item in the implementation plan, not a footnote here.

---

## 16. Traceability

| Decision | PRD feature or criterion it satisfies |
|---|---|
| T1 Hosting | C1 (zero cost), the 55-second budget (§6.1), F3-AC6, F5 (SHAP survives 16 GB) |
| T2 Raw SQL + migrations | C2, F9-AC1, F8-AC6 (fail fast at start) |
| T3 Server sessions | F8, F8-AC2, F9-AC1, F7-AC2 |
| T4 Streaming single request | F3-AC6, F12-AC3, the 55-second budget in §6.1 |
| T5 ML stack | F3-AC1, F3-AC2, F3-AC5, F5-AC5, §8.3 confidence intervals |
| T6 REST + problem+json | F1-AC6, F4-AC1, F12, all error-copy requirements |
| T7 Same-origin proxy | F8 session reliability, C4 (stack), F7-AC1 |
| T8 Tailwind + shadcn + Recharts | F4, F5, the accessibility requirements behind colour-not-alone |
| T9 Postgres counters + cache | F12-AC1..AC4, F10-AC6 |
| T10 Full pipeline | S1 (sample fidelity), S3 (traceability), S5 (honesty), S6 (degradation) |
| File re-uploaded per request (§3) | C3, F6-AC6, F7-AC3, PRD §10 |
| No down-migrations (§4) | C2, decided cost recorded rather than hidden |
| No CSRF token (§9.1) | Follows from T7; the mechanism it guards against is closed by origin + `SameSite` |

---

## Appendix A — Alternatives considered and rejected

| Rejected | Why |
|---|---|
| **Oracle Cloud Always Free** (4 ARM cores, 24 GB, always-on) | Objectively better hardware, and it requires a card for identity verification — excluded by C1. The real decision behind T1, recorded here so it is not re-litigated |
| **Hugging Face Docker Space** | $9/month PRO on a card. Excluded by C1. The free Gradio SDK runs the same FastAPI app in the same process, so nothing but the packaging changes |
| **Render / Koyeb free** (512 MB) | Cannot hold pandas + scikit-learn + SHAP; would force deleting F5's feature influence |
| **Vercel serverless Python** | 250 MB bundle, 10 s Hobby timeout — cannot host this backend at all |
| **PythonAnywhere free** | No outbound internet, so no LLM and no reset mail |
| **Cloudflare Workers** | 128 MB isolate, no pandas |
| **Alembic** | Built around SQLAlchemy; heavy dependency and its conventions just to run our own SQL files |
| **SQLAlchemy Core** | Emits SQL at runtime, so the reviewer reads Python instead of the queries. Contradicts "screams SQL" |
| **JWT (stateless, or in localStorage)** | Revocation is required three times over; a denylist table is a session table with worse ergonomics. localStorage additionally hands any XSS an account |
| **Background job + polling / SSE** | Adds a status machine, orphan recovery and polling for a job that takes ten seconds |
| **EventSource** | GET-only; cannot carry a file |
| **Hand-rolled fairness metrics** | The definitions have edge cases (empty groups, zero positives) that silently invert a verdict. Importing the reference implementation is the cheaper correctness |
| **Upstash Redis** | A second vendor to solve what one `ON CONFLICT DO UPDATE` solves |
| **Material UI / Chakra** | Instantly recognisable as a template, and its opinions cost more to override than they save |
| **Vercel route handlers as a BFF** | Hobby execution limits are shorter than one analysis |
| **Server-side PDF generation** | Print-to-PDF is free, already in the browser, and produces a document the user can edit |
| **Storing the uploaded file** | The product's privacy claim is the product |

---

*End of TRD v2.4. The Implementation Plan is written and starts after day zero.*
