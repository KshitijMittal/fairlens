# FairLens v2 — Backend Schema

| | |
|---|---|
| **Version** | 2.2 (29 Oct: anonymous sample rule, repairs refresh scope, repairs read query) |
| **Status** | Decisions closed (8 of 8). Implementation Plan written. |
| **Date** | 28 October 2026 |
| **Baseline** | `docs/PRD.md` (v2.2 incl. §8.5 correction), `docs/TRD.md` (v2.3), `docs/APP_FLOW.md` (v2.2), `docs/UI_UX.md` (v2.2) |
| **Companion** | `backend/app/db/migrations/*.sql` — this document is the specification; those files are the implementation |
| **Next document** | `docs/IMPLEMENTATION_PLAN.md` (written; a change here requires a matching change there) |

---

## 0. How to read this document

- **Sections 1–3** are the rules: conventions, the entity map, and the three invariants everything else depends on.
- **Sections 4–9** are the actual DDL, migration by migration, in the order they run. This is the part a reviewer opens.
- **Section 10** is deletion, the one operation that must reach every table.
- **Section 11** is `AnalysisResult`, the one payload both the summary and the technical view read.
- **Section 12** is the streaming frame schema, including the fold variant.
- **Sections 13–16** are the query catalogue, the index rationale, what must never be stored, and traceability.

Every table and column name here is the name used in code. If a query disagrees with this document, one of them is a bug.

### 0.1 The eight decisions this document implements

Each was decided in the one-question loop, not inherited from an earlier draft. Where a decision changed the draft, the change is named.

| # | Decision | Consequence |
|---|---|---|
| **S1** | Hybrid: checks and groups are rows; metadata stays `jsonb` | Constraints reject nonsense rates and "inconclusive with no reason". The justification is integrity, not a reporting query nobody will run |
| **S2** | Narrative in its own table | `analyses` is written once and never updated; a slow LLM cannot hold the transaction open |
| **S3** | A trigger rejects **every** update | A stored number cannot be edited by a bug, a script or a migration. Fixed data is deleted and re-run |
| **S4** | A repair is an ordinary `analyses` row with `parent_id` + `repair_strategy` | One read path, one payload shape. History reads a view, so the "top level only" filter cannot be dropped |
| **S5** | Rate-limit identifiers are `sha256(pepper ‖ ip)` | The counter table cannot become a visitor log |
| **S6** | The server authors every sentence containing a figure | One place formats numbers. Copy changes are backend deploys |
| **S7** | `deciding_checks text[]` — every check at the deciding state, empty on a Pass | Honest about ties. It is derived data and is treated as a cache with an owner (§3.3) |
| **S8** | The JSON export is assembled from the tables on demand | One definition of a result; nothing is stored twice |

The verdict rule changed with the PRD (§8.5): `Fail > Inconclusive > Warn > Pass`, and "core" no longer influences the verdict. That correction is what `deciding_checks` is built around — a Pass can no longer coexist with an unjudgeable check.

---

## 1. Conventions

| Rule | Detail |
|---|---|
| Naming | `snake_case`, plural table names, singular column names, no abbreviations except `id`, `ci`, `n` |
| Primary keys | `uuid` with `gen_random_uuid()` for things a user can reference (`users`, `analyses`); `text` for token hashes, because the hash *is* the key |
| Timestamps | `timestamptz not null default now()`, always UTC. Never `timestamp` — a fairness report with an ambiguous date is a small lie |
| Booleans | `not null` with an explicit default. No nullable booleans: three-valued logic in a check column is how states go missing |
| Enumerations | `text` plus a `check` constraint, never a Postgres `enum` type. Enum types cannot be altered without a migration dance, and the vocabulary here will grow |
| Numbers | `double precision` for rates and metrics (they are estimates, not money); `integer` for counts; no `numeric` anywhere |
| Nullability | Nullable only where absence means something specific and is documented. A nullable column with no documented meaning is a defect |
| Case | Emails are stored as given and compared with `lower(email)` through a unique index |
| No soft deletes | A deleted row is gone. No `deleted_at`, no archive, no tombstone |
| Extensions | None required. `gen_random_uuid()` is core in Postgres 13+, and the deployment runs 16 |

---

## 2. Entity map

```
users ─┬─< sessions
       ├─< auth_tokens            (password reset)
       └─< analyses ─┬─< analysis_checks      (exactly 5)
                     ├─< analysis_groups      (one row per group per scope; 2 scopes)
                     ├─< analysis_narratives  (0 or 1)
                     ├─< analysis_repairs     (0..3, one per strategy)
                     ├─< chat_messages
                     ├─< shares
                     └─< analyses             (parent_id: a repair's child analysis)

top_level_analyses   (view over analyses, parent_id is null)

rate_limits     (no foreign keys — counters, keyed by bucket + identifier)
llm_cache       (optional FK to analyses, cascade)
schema_migrations (the runner's own bookkeeping)
```

**Two shapes worth noting before the DDL.** `analysis_checks` and `analysis_groups` are relational because they are the numbers the product is about, and because a table is the only place a `check` constraint can reject a `selection_rate` of 1.4 or an Inconclusive state with no reason. `model_card`, `encoding`, `thresholds`, `proxies` and `sampling` are `jsonb` because they are always read whole, never filtered, and turning them into eight more tables would add joins and enforce nothing.

---

## 3. The three invariants

Everything below either supports these or is neutral to them.

### 3.1 No row data, ever

No column anywhere holds a value from the uploaded file, a cell, a row, a repaired dataset, or a file's bytes. What is stored is: column **names**, counts, rates, intervals, thresholds, model metadata, and prose. A test asserts this by shape — any new `text`/`jsonb` column that could hold arbitrary user content must be on an approved list.

`analyses.source_sha256` stores a fingerprint of the file, not the file. It exists so a repair can prove it is rebuilding the same dataset (App Flow A6).

### 3.2 Metrics are immutable

`analyses`, `analysis_checks`, `analysis_groups` and `analysis_repairs` reject `UPDATE` at the database level, not by convention. Deletion still cascades, so account deletion works, but a stored number cannot be edited by a bug, a migration, or a well-meaning script.

`analysis_repairs` is in that list because it was the one gap in the draft: refreshing a repair comparison would have upserted into it, making it the only analysis-derived table where a number could change. Refresh is now `DELETE` + `INSERT` in one transaction (see `0008` below).

### 3.3 `deciding_checks` is a cache, with one owner

`analyses.deciding_checks` repeats a fact that also lives in `analysis_checks.state`. That duplication is deliberate — history lists need it without a join — and it is a cache, not a second source of truth.

- **Owner:** the verdict function in `backend/app/core/verdict.py`. Nothing else writes the column.
- **Shape:** the check codes at the state that decided the verdict, in `C1`–`C5` order. `Fail` → every failing check; `Warn` → every warning; `Inconclusive` → every inconclusive check; `Pass` → empty.
- **Consistency test:** runs in CI against a real Postgres and fails if the column ever disagrees with the rows:

```sql
select a.id
from analyses a
where a.deciding_checks <> case
  when a.verdict = 'pass' then '{}'::text[]
  else (
    select coalesce(array_agg(c.check_code order by c.check_code), '{}')
    from analysis_checks c
    where c.analysis_id = a.id and c.state = a.verdict
  )
end;
```

Zero rows expected. The database can check the column's shape and its agreement with the verdict (below); only this test can check it against the check rows.

---

## 4. Migration list

| # | File | Creates |
|---|---|---|
| 0001 | `0001_users.sql` | `users` |
| 0002 | `0002_sessions.sql` | `sessions` |
| 0003 | `0003_auth_tokens.sql` | `auth_tokens` |
| 0004 | `0004_analyses.sql` | `analyses` |
| 0005 | `0005_analysis_checks.sql` | `analysis_checks` |
| 0006 | `0006_analysis_groups.sql` | `analysis_groups` |
| 0007 | `0007_analysis_narratives.sql` | `analysis_narratives` |
| 0008 | `0008_analysis_repairs.sql` | `analysis_repairs` |
| 0009 | `0009_chat_messages.sql` | `chat_messages` |
| 0010 | `0010_shares.sql` | `shares` |
| 0011 | `0011_rate_limits.sql` | `rate_limits` |
| 0012 | `0012_llm_cache.sql` | `llm_cache` |
| 0013 | `0013_top_level_analyses.sql` | the history view |
| 0014 | `0014_immutability.sql` | the update-rejection function and four triggers |

Before any of these, the runner creates its own table — it is not a migration, because the runner needs it to know which migrations to run:

```sql
create table if not exists schema_migrations (
  version    text primary key,
  checksum   text not null,
  applied_at timestamptz not null default now()
);
```

---

## 5. Identity and sessions

### 0001_users.sql

```sql
create table users (
  id                  uuid primary key default gen_random_uuid(),
  email               text not null,
  password_hash       text,
  google_sub          text,
  display_name        text,
  password_changed_at timestamptz not null default now(),
  created_at          timestamptz not null default now(),

  constraint users_email_shape
    check (position('@' in email) > 1 and length(email) <= 320),

  -- A user must be able to authenticate somehow.
  constraint users_has_a_method
    check (password_hash is not null or google_sub is not null)
);

create unique index users_email_lower_uniq on users (lower(email));
create unique index users_google_sub_uniq  on users (google_sub)
  where google_sub is not null;
```

| Column | Why |
|---|---|
| `password_hash` nullable | Google-only accounts have no password. The hash is argon2id, or bcrypt if the host cannot install argon2 (TRD §5.3) |
| `google_sub` nullable and unique | Google's stable subject identifier. The email is not an identifier — addresses change hands |
| `password_changed_at` | Reset tokens issued before this instant are dead. One column replaces a token-invalidation table |
| `display_name` | Shown in the header. Never used for authorisation |

Both unique indexes are partial or expression indexes rather than table constraints, because both rules are about *normalised* values and *presence*, which `unique` alone cannot express.

### 0002_sessions.sql

```sql
create table sessions (
  token_hash text primary key,
  user_id    uuid not null references users(id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  last_seen_at timestamptz,

  constraint sessions_expiry_after_creation check (expires_at > created_at)
);

create index sessions_user_idx   on sessions (user_id);
create index sessions_expiry_idx on sessions (expires_at);
```

- `token_hash` is the primary key: lookup is a single index probe and there is nothing to compare in constant time, because the raw token is not stored.
- `sessions_user_idx` makes "sign out everywhere" one `DELETE` on a small index rather than a scan.
- `sessions_expiry_idx` makes the sweep (`DELETE ... WHERE expires_at < now()`) cheap. It runs at container start and on login (TRD §5.1) — no cron.
- `last_seen_at` is written at most once per hour per session. Without that cap it would turn every request into a write.

### 0003_auth_tokens.sql

```sql
create table auth_tokens (
  token_hash text primary key,
  user_id    uuid not null references users(id) on delete cascade,
  purpose    text not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  used_at    timestamptz,

  constraint auth_tokens_purpose check (purpose in ('password_reset')),
  constraint auth_tokens_expiry_after_creation check (expires_at > created_at)
);

create index auth_tokens_user_idx on auth_tokens (user_id);
```

`purpose` exists with exactly one value today. It is there so that adding invite or email-verification tokens later does not require a second table with an identical shape.

A token is valid when `used_at is null`, `expires_at > now()`, and `created_at > users.password_changed_at`. The last condition is what makes a password change invalidate outstanding resets without deleting rows.

---

## 6. The analysis

### 0004_analyses.sql

```sql
create table analyses (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references users(id) on delete cascade,

  -- A repair produces a child analysis, so the comparison is a real row
  -- rather than a claim in prose (PRD F6).
  parent_id       uuid references analyses(id) on delete cascade,
  repair_strategy text,

  dataset_name   text not null,
  source_sha256  text not null
                 check (source_sha256 ~ '^[0-9a-f]{64}$'),
  is_sample      boolean not null default false,
  sample_slug    text,

  row_count      integer not null check (row_count >= 50),
  column_count   integer not null check (column_count between 2 and 60),
  columns        jsonb   not null,   -- [{name, inferred_type}] only, never values

  outcome_column text not null,
  positive_value text not null,
  group_column   text not null,
  group_count    smallint not null check (group_count between 2 and 10),
  age_banding    boolean not null default false,

  sampling       jsonb,              -- null when the whole file was analysed
  thresholds     jsonb not null,     -- echoed back with every result (F3-AC3)
  model_card     jsonb not null,
  encoding       jsonb not null,
  proxies        jsonb not null default '[]'::jsonb,

  verdict         text not null,
  -- Every check at the state that decided the verdict, C1..C5. Empty on a Pass.
  -- A cache owned by verdict.py; the consistency test lives in §3.3.
  deciding_checks text[] not null default '{}',

  seed           bigint  not null,
  engine_version text    not null,
  duration_ms    integer not null check (duration_ms >= 0),
  created_at     timestamptz not null default now(),

  constraint analyses_verdict
    check (verdict in ('fail', 'warn', 'inconclusive', 'pass')),

  -- A Pass with a deciding check, and a non-Pass with none, are both impossible.
  constraint analyses_deciding_checks_pass
    check ((verdict = 'pass') = (cardinality(deciding_checks) = 0)),

  constraint analyses_deciding_checks_vocabulary
    check (deciding_checks <@ array['C1','C2','C3','C4','C5']::text[]),

  -- At most five codes. Duplicates are prevented by the owner (§3.3):
  -- a check constraint cannot run the subquery that would detect them.
  constraint analyses_deciding_checks_length
    check (cardinality(deciding_checks) <= 5),

  constraint analyses_repair_strategy
    check (repair_strategy is null
           or repair_strategy in ('reweigh', 'resample', 'drop_proxies')),

  constraint analyses_parent_only_for_repairs
    check ((parent_id is null) = (repair_strategy is null))
);

create index analyses_user_created_idx on analyses (user_id, created_at desc);
create index analyses_parent_idx       on analyses (parent_id)
  where parent_id is not null;
create index analyses_sample_idx       on analyses (is_sample)
  where is_sample;
```

| Column | Why |
|---|---|
| `parent_id` + `repair_strategy` | F6 requires a repair to create a child analysis, and F9 requires the chosen repair to be saved. The pairing constraint means a child row cannot exist without saying what produced it |
| `deciding_checks` | S7. An array rather than one column, because a Fail with two failing checks has two reasons and picking one would present an arbitrary choice as a fact |
| `deciding_checks` empty on a Pass | Enforced by `analyses_deciding_checks_pass`. Under §8.5 a Pass means every check was judged and passed, so there is nothing to name |
| `group_count` between 2 and 10 | Enforced in the database as well as the parser, because a bug that lets eleven groups through would break the layout and the checks |
| `columns` jsonb | Names and types only. This is what the technical view and the fingerprint check read |
| `seed` | The derived seed (TRD §6.2). Stored so a golden test can prove reproducibility, and so a repair can reuse the fold assignment (F6-AC2) |
| `duration_ms` | Shown on the model card; also the first place to look when someone reports a slow run |

**Duplicates inside the array are prevented by the owner, not by a constraint.** A `check` cannot run a subquery, so `array['C1','C1']` would pass the vocabulary and length checks. `verdict.py` builds the array from the check rows, so a duplicate means the verdict function itself is wrong — the §3.3 consistency test catches that, and it is the only place it could arise.

**Anonymous sample runs never reach this table.** `user_id` is `NOT NULL` on purpose: there is no row without an owner. An anonymous sample result lives in the API process's in-memory cache (TRD §8.1, Implementation Plan P2) and expires within 30 minutes, which is what makes F9-AC5 true without a nullable owner column.

### 0005_analysis_checks.sql

```sql
create table analysis_checks (
  analysis_id uuid not null references analyses(id) on delete cascade,
  check_code  text not null,
  state       text not null,
  value       double precision,
  ci_low      double precision,
  ci_high     double precision,
  threshold   jsonb not null,
  reason      text,

  primary key (analysis_id, check_code),

  constraint analysis_checks_code
    check (check_code in ('C1', 'C2', 'C3', 'C4', 'C5')),
  constraint analysis_checks_state
    check (state in ('pass', 'warn', 'fail', 'inconclusive')),
  constraint analysis_checks_interval
    check (ci_low is null or ci_high is null or ci_low <= ci_high),
  -- An inconclusive check always says why, and a decided one never does.
  constraint analysis_checks_reason
    check ((state = 'inconclusive') = (reason is not null)),
  constraint analysis_checks_reason_vocabulary
    check (reason is null or reason in (
      'group_too_small', 'interval_too_wide',
      'no_positives', 'no_negatives'))
);
```

Five rows per analysis, enforced by the application and asserted by a test — a `check` constraint cannot count rows, and a trigger to enforce "exactly five" would fire on every insert of a batch and cost more than it protects.

`threshold` is `jsonb` because the shape differs per check (a ratio band for C1, a signed difference for C3) and because it is echoed to the client verbatim so the UI never hardcodes a limit (F3-AC3).

`reason` uses a closed vocabulary, not prose, so the UI can translate it and so an inconclusive state can be counted across analyses. The `check` constraint above makes "inconclusive without a reason" and "decided with a reason" both impossible.

### 0006_analysis_groups.sql

```sql
create table analysis_groups (
  analysis_id    uuid not null references analyses(id) on delete cascade,
  scope          text not null,
  group_label    text not null,
  n              integer not null check (n >= 0),
  positives      integer not null check (positives >= 0),
  selection_rate double precision not null
                 check (selection_rate >= 0 and selection_rate <= 1),
  rate_ci_low    double precision,
  rate_ci_high   double precision,
  tpr            double precision check (tpr is null or tpr between 0 and 1),
  fpr            double precision check (fpr is null or fpr between 0 and 1),
  accuracy       double precision check (accuracy is null or accuracy between 0 and 1),

  primary key (analysis_id, scope, group_label),

  constraint analysis_groups_scope check (scope in ('historical', 'model')),
  constraint analysis_groups_positives check (positives <= n),
  constraint analysis_groups_interval
    check (rate_ci_low is null or rate_ci_high is null
           or rate_ci_low <= rate_ci_high)
);
```

Two scopes, `historical` and `model`, in one table rather than two tables with identical columns. The chart draws one row per group per scope, and the per-group table in the technical view draws the same rows — which means the two views literally cannot disagree.

`tpr` is null when a group has no negatives or no positives; that null is what produces the `no_positives` / `no_negatives` inconclusive reason rather than a fabricated zero. Under the corrected §8.5 rule, that null now decides the whole verdict rather than only a side note.

### 0007_analysis_narratives.sql

```sql
create table analysis_narratives (
  analysis_id uuid primary key references analyses(id) on delete cascade,
  kind        text not null,
  body        text not null,
  provider    text,
  model_name  text,
  created_at  timestamptz not null default now(),

  constraint analysis_narratives_kind check (kind in ('template', 'ai')),
  constraint analysis_narratives_provider
    check ((kind = 'ai') = (provider is not null))
);
```

A separate table rather than a column on `analyses`, for one reason: `analyses` is immutable (§3.2), and the narrative arrives after the metrics at the narration stage (TRD §6.1 stage 7). Splitting it keeps the immutability trigger on `analyses` honest instead of carving out a column-level exception — the exact exception that turns into a hole two years later.

`kind = 'template'` is a first-class result, not a failure state (PRD C5), and `provider` records which model wrote the prose — or nothing, when no model did.

---

## 7. Repairs, chat and sharing

### 0008_analysis_repairs.sql

```sql
create table analysis_repairs (
  analysis_id         uuid not null references analyses(id) on delete cascade,
  strategy            text not null,
  changed_rows        integer,
  changed_columns     jsonb   not null default '[]'::jsonb,
  dropped_columns     jsonb   not null default '[]'::jsonb,
  parity_after        double precision,
  amplification_after double precision,
  tpr_gap_after       double precision,
  accuracy_after      double precision,
  verdict_after       text,
  recommended         boolean not null default false,
  summary             text not null,
  created_at          timestamptz not null default now(),

  primary key (analysis_id, strategy),

  constraint analysis_repairs_strategy
    check (strategy in ('reweigh', 'resample', 'drop_proxies')),
  constraint analysis_repairs_verdict_after
    check (verdict_after is null
           or verdict_after in ('fail', 'warn', 'inconclusive', 'pass'))
);

create index analysis_repairs_recommended_idx on analysis_repairs (analysis_id)
  where recommended;
```

`summary` is server-authored prose, like the narratives, and stores the one plain sentence shown in the comparison table. `recommended` is a boolean rather than a ranking, because F6-AC4 permits at most one recommendation and usually none — and a partial index makes "which strategy was recommended" a cheap read.

**Immutable, so refresh is `DELETE` + `INSERT`.** The table carries the §3.2 trigger, which is why there is no `ON CONFLICT DO UPDATE` path:

```sql
-- one transaction
delete from analysis_repairs where analysis_id = %(analysis_id)s;
insert into analysis_repairs (...) values (...), (...), (...);
```

Re-running the three strategies replaces all three rows, so a stale recommendation cannot survive a refresh. A partial refresh (one strategy only) would leave the comparison disagreeing with itself and is not offered. The same transaction also deletes the parent's three child `analyses` rows and inserts three fresh ones, so a re-run leaves exactly three children as well as exactly three comparison rows. Adding a set instead would grow storage on every click and leave the old children reachable by id. An anonymous sample run has no parent row, so its comparison exists only in the in-memory result and never reaches this table.

### 0009_chat_messages.sql

```sql
create table chat_messages (
  id          bigint generated always as identity primary key,
  analysis_id uuid not null references analyses(id) on delete cascade,
  role        text not null,
  body        text not null,
  citations   jsonb not null default '[]'::jsonb,
  created_at  timestamptz not null default now(),

  constraint chat_messages_role check (role in ('user', 'assistant'))
);

create index chat_messages_analysis_idx
  on chat_messages (analysis_id, created_at);
```

`citations` holds the metric keys the answer drew on, so a reviewer can check that a claim came from the stored payload rather than from the model (F10). An empty array means the answer cited nothing, which is itself a signal.

Chat messages are not covered by the immutability trigger: a transcript is conversation, not a stored result. Only the owner's turns are stored — a share viewer's question is answered and discarded, so a stranger's words never appear in the owner's transcript or in a history row.

### 0010_shares.sql

```sql
create table shares (
  token_hash     text primary key,
  analysis_id    uuid not null references analyses(id) on delete cascade,
  created_at     timestamptz not null default now(),
  last_viewed_at timestamptz,
  view_count     integer not null default 0 check (view_count >= 0)
);

create index shares_analysis_idx on shares (analysis_id);
```

Revocation is `DELETE`, so the table has no `revoked` column and no expiry column. A revoked link and an invented link are indistinguishable to a visitor, which is the point (App Flow §4.3).

`view_count` is incremented with the same `UPDATE ... RETURNING` pattern as the rate limiter, so a viewer loading the page twice cannot produce a lost update.

---

## 8. Abuse and cost control

### 0011_rate_limits.sql

```sql
create table rate_limits (
  bucket       text not null,
  identifier   text not null,
  window_start timestamptz not null,
  count        integer not null default 0 check (count >= 0),

  primary key (bucket, identifier, window_start)
);

create index rate_limits_window_idx on rate_limits (window_start);
```

The counter statement, verbatim:

```sql
insert into rate_limits (bucket, identifier, window_start, count)
values (%(bucket)s, %(identifier)s, date_trunc('hour', now()), 1)
on conflict (bucket, identifier, window_start)
do update set count = rate_limits.count + 1
returning count;
```

- `identifier` is a SHA-256 of `pepper || ip` for anonymous buckets and the user id for authenticated ones. The raw IP is never stored, so the table cannot be turned into a log of who visited.
- **This is pseudonymisation, not anonymisation.** Someone holding both the pepper and the table could brute-force a small IPv4 space. The claim is that the table alone is useless, and the pepper lives in the same environment as every other secret.
- The primary key is the whole lookup: one index probe, one atomic increment, no race and no `select` before the write.
- `rate_limits_window_idx` serves the sweep of windows older than a day.

### 0012_llm_cache.sql

```sql
create table llm_cache (
  key_hash       text primary key,
  analysis_id    uuid references analyses(id) on delete cascade,
  kind           text not null,
  prompt_version text not null,
  response       jsonb not null,
  created_at     timestamptz not null default now(),

  constraint llm_cache_kind check (kind in ('narrative', 'chat'))
);

create index llm_cache_analysis_idx on llm_cache (analysis_id)
  where analysis_id is not null;
```

`analysis_id` is nullable because a chat answer is only cacheable when it belongs to an analysis — and because a cache row must never outlive the report it quotes. The cascade enforces that by construction.

`prompt_version` inside the key means editing a prompt misses old cache entries automatically, with no flush step (TRD §10.2). A stored narrative is not rewritten: a new prompt applies to new analyses.

---

## 9. Views and immutability

### 0013_top_level_analyses.sql

```sql
create view top_level_analyses
with (security_invoker = true) as
select id, user_id, dataset_name, is_sample, row_count, column_count,
       verdict, deciding_checks, engine_version, duration_ms, created_at
from analyses
where parent_id is null;
```

S4 nests repair children under their parent, which means every history read needs `parent_id is null`. A filter written in one query file is a filter someone deletes during a refactor, and the failure is silent: a repair appears in history as an unrelated upload. The view makes it structural.

It lists its columns explicitly rather than `select *`, so adding a column to `analyses` does not silently widen what history can expose.

`security_invoker = true` (Postgres 15+) makes the view run with the caller's privileges rather than the owner's. The app uses one role, so this changes nothing today; it keeps the view from becoming a privilege-escalation foot-gun if a read-only role is ever added.

The view is **not** a security boundary. Every query against it still filters by `user_id`.

### 0014_immutability.sql

```sql
create or replace function reject_metric_update() returns trigger
language plpgsql as $$
begin
  raise exception
    'fairlens: % is immutable; delete the analysis and run it again', tg_table_name
    using errcode = 'restrict_violation';
end;
$$;

create trigger analyses_immutable
  before update on analyses
  for each row execute function reject_metric_update();

create trigger analysis_checks_immutable
  before update on analysis_checks
  for each row execute function reject_metric_update();

create trigger analysis_groups_immutable
  before update on analysis_groups
  for each row execute function reject_metric_update();

create trigger analysis_repairs_immutable
  before update on analysis_repairs
  for each row execute function reject_metric_update();
```

`before update` only. `before delete` would block the `ON DELETE CASCADE` that account deletion depends on (F9-AC1), which would turn a privacy feature into a broken one.

The message names no row id. The draft's version read `old.id`, which does not exist on `analysis_checks` or `analysis_groups` — the trigger would have raised a `record "old" has no field "id"` error instead of the intended one, on the first update attempt. The table name is enough to find the bug.

**What this costs, stated plainly:** a wrong number cannot be patched. The fix is to delete the analysis and run it again, which is also the only fix that keeps the report honest about which engine version produced it. If a future feature wants to rename a dataset or attach a tag, it gets its own table, not a column on `analyses`.

---

## 10. Cascade and deletion

Every table that references a user or an analysis answers to one of two rules.

| Deletion | Cascades to |
|---|---|
| `users` row deleted | `sessions`, `auth_tokens`, `analyses` |
| `analyses` row deleted | `analysis_checks`, `analysis_groups`, `analysis_narratives`, `analysis_repairs`, `chat_messages`, `shares`, `llm_cache`, and child analyses through `parent_id` |
| `shares` row deleted | nothing — the link simply stops resolving |

**The deletion test** (F9-AC1), which runs in CI against a real Postgres:

```sql
-- Before: one account with one analysis, a share, three chat messages,
-- a narrative and three repairs.
delete from users where id = %(user_id)s;

-- After: every count must be zero.
select
  (select count(*) from sessions            where user_id      = %(user_id)s) as sessions,
  (select count(*) from auth_tokens         where user_id      = %(user_id)s) as tokens,
  (select count(*) from analyses            where user_id      = %(user_id)s) as analyses,
  (select count(*) from analysis_checks     where analysis_id  = %(analysis_id)s) as checks,
  (select count(*) from analysis_groups     where analysis_id  = %(analysis_id)s) as groups,
  (select count(*) from analysis_narratives where analysis_id  = %(analysis_id)s) as narratives,
  (select count(*) from analysis_repairs    where analysis_id  = %(analysis_id)s) as repairs,
  (select count(*) from chat_messages       where analysis_id  = %(analysis_id)s) as chats,
  (select count(*) from shares              where analysis_id  = %(analysis_id)s) as shares,
  (select count(*) from llm_cache           where analysis_id  = %(analysis_id)s) as cache;
```

Ten zeros. The test asserts all of them, individually — a single total would pass while a table was quietly missed. The fixture must also include a **repair child analysis**, because `parent_id` cascade is the one path that can deadlock or recurse if the trigger is ever changed to `before delete`. Because the query above counts the parent's child rows, the test captures the child's id before deletion and runs the same five `analysis_id` counts against it, so a cascade that stops at the child is caught rather than hidden.

`rate_limits` is deliberately not in that list: it holds no user data, and the counters expire on their own.

---

## 11. `AnalysisResult` — the payload both views read

One object, returned by the final stream frame, by `GET /v1/analyses/{id}`, and by `GET /v1/shared/{token}`. The summary view and the technical view read the **same** object, which is what makes F4-AC2 and F5-AC2 true by construction rather than by discipline.

```jsonc
{
  "id": "3f2b…",
  "created_at": "2026-10-27T09:14:22Z",
  "engine_version": "2.0.0",
  "duration_ms": 8421,

  "dataset": {
    "name": "loans.csv",
    "sha256": "9c1f…",
    "rows": 900,
    "columns": 8,
    "column_names": ["applicant_id", "…"],
    "is_sample": false,
    "sample": null
  },

  "confirmation": {
    "outcome":  { "column": "approved", "positive_value": "yes", "positive_count": 612 },
    "groups":   { "column": "gender",
                  "values": [ { "label": "female", "n": 318 },
                              { "label": "male",   "n": 582 } ] },
    "age_banding": { "applied": true,
                     "bands": ["18–24","25–34","35–44","45–54","55–64","65+"] },
    "factor_columns": 6
  },

  "verdict": "fail",
  "deciding_checks": ["C1"],

  "lead": {
    "state": "fail",
    "headline": "This data would teach a model to treat people unequally.",
    "consequence": "One or more of the five checks failed. Training on this data as it is would reproduce the disparity the data already contains."
  },

  "checks": [
    {
      "code": "C1",
      "name": "Historical disparity",
      "core": true,
      "state": "fail",
      "value": 0.66,
      "interval": [0.58, 0.74],
      "threshold": { "pass_at": 0.90, "warn_at": 0.80, "direction": "above" },
      "sentence": "The decisions already in your data do not treat these groups equally.",
      "reason": null
    }
  ],

  "groups": {
    "historical": [
      { "label": "male",   "n": 582, "positives": 361, "selection_rate": 0.62,
        "interval": [0.58, 0.66], "tpr": 0.71, "fpr": 0.18, "accuracy": null },
      { "label": "female", "n": 318, "positives": 130, "selection_rate": 0.41,
        "interval": [0.36, 0.46], "tpr": 0.55, "fpr": 0.21, "accuracy": null }
    ],
    "model": [
      { "label": "male",   "n": 582, "positives": 375, "selection_rate": 0.64,
        "interval": [0.60, 0.68], "tpr": 0.74, "fpr": 0.20, "accuracy": 0.79 },
      { "label": "female", "n": 318, "positives": 95,  "selection_rate": 0.30,
        "interval": [0.25, 0.35], "tpr": 0.49, "fpr": 0.19, "accuracy": 0.76 }
    ]
  },

  "affected": [
    { "group": "women",
      "sentence": "Women were approved at 41% and men at 62% — a 21-point gap (95% CI 14–28)." }
  ],

  "amplification": {
    "sentence": "The model makes the gap wider.",
    "detail": "Your data already approves men at 62% and women at 41% — a 21-point gap. A model trained on it widens that gap to 34 points. It learned the pattern and pushed harder than the data did.",
    "historical_gap": 0.21,
    "model_gap": 0.34,
    "difference": 0.13
  },

  "model_card": {
    "algorithm": "logistic_regression",
    "hyperparameters": { "max_iter": 1000, "solver": "lbfgs", "class_weight": null },
    "folds": 5,
    "oof_accuracy": 0.78,
    "oof_precision": 0.74,
    "oof_recall": 0.71,
    "positive_label": "yes",
    "sensitive_as_feature": true,
    "engine_version": "2.0.0"
  },

  "encoding": {
    "categorical": [ { "column": "region", "mapping": { "north": 0, "south": 1 } } ],
    "numeric":     [ { "column": "income", "imputed_median": 41250 } ],
    "dropped":     [ { "column": "applicant_id", "reason": "identifier" } ],
    "grouped_rare": [ { "column": "job_title", "kept": 30 } ]
  },

  "proxies": [
    { "column": "postcode",   "measure": "cramers_v",        "value": 0.41 },
    { "column": "job_title",  "measure": "cramers_v",        "value": 0.33 }
  ],

  "sampling": null,

  "thresholds": {
    "parity": { "pass_at": 0.90, "warn_at": 0.80 },
    "amplification": { "warn_at": 0.05, "fail_at": 0.15 },
    "equal_opportunity": { "pass_at": 0.05, "fail_at": 0.15 },
    "bootstrap": { "resamples": 1000, "confidence": 0.95, "max_half_width": 0.10 },
    "min_group_rows": 30
  },

  "narrative": {
    "kind": "template",
    "body": "…",
    "provider": null
  }
}
```

### Rules attached to this contract

| Rule | Why |
|---|---|
| **Every sentence containing a number is authored by the server.** `lead.headline`, `lead.consequence`, `checks[].sentence`, `affected[].sentence`, `amplification.sentence`, `amplification.detail`, `narrative.body` and `analysis_repairs.summary` arrive as finished strings | F4-AC6: the client renders these verbatim and never composes the text around a figure. The copy therefore lives in `backend/app/core/report_text.py` |
| `checks[]` always has exactly five entries, in `C1`–`C5` order | An omitted check is how an Inconclusive state disappears |
| `deciding_checks` equals the codes whose `state` matches the verdict, and is `[]` on a Pass | It is the stored column, not recomputed by the client. History and the lead block read the same list |
| `lead.headline` is chosen by `verdict`, never by the number of failing checks | One verdict, one sentence. A Fail with one failing check does not get softer copy |
| `groups.historical` and `groups.model` have the same labels in the same order | The chart aligns them by index; a mismatch would silently mis-pair bars |
| `interval` is `null` or a two-element ascending array | The UI renders a whisker only when it exists |
| `thresholds` is echoed in full | F3-AC3: the UI never hardcodes a limit |
| `sampling` is `null` or an object naming the row cap used | F1-AC7: sampling is recorded and repeated on the report and in the JSON |
| `narrative` is never `null` | If no `analysis_narratives` row exists, the builder returns the template with `kind: "template"`. F4-AC4 is structural, not a promise the database can quietly break |
| No field ever holds a cell value | §3.1 |
| The JSON export is this object, serialised | F5-AC4: no client-side recomputation. S8: built from the tables on every read |

**One consequence worth stating.** Because the copy is server-authored, changing a sentence is a backend deploy, not a frontend one. That is the right trade for a product whose central claim is that no number is invented client-side — but it does mean `report_text.py` and `UI_UX.md` §7 must be kept in step, and a test asserts that both forms of every check sentence and the four lead headlines match the specification verbatim.

---

## 12. Streaming frames

`Content-Type: application/x-ndjson`, one JSON object per line (TRD §7).

```jsonc
{"event":"stage","stage":"parsing","index":1,"total":6,"label":"Reading your file…"}

{"event":"stage","stage":"training","index":3,"total":6,"label":"Training a model on your data…"}

{"event":"stage","stage":"training","index":3,"total":6,
 "label":"Training fold 3 of 5…","fold":3,"folds":5}

{"event":"ping"}

{"event":"result","payload":{ /* AnalysisResult */ }}

{"event":"error","problem":{ /* RFC 9457, identical to a JSON error body */ }}
```

| Field | Rule |
|---|---|
| `stage` | One of `parsing`, `cleaning`, `training`, `measuring`, `influence`, `saving` |
| `index` / `total` | Position in the pipeline, 1-based. `total` is always 6 |
| `label` | The exact string to display, sent by the server so the copy has one home (§11). The client never maps a stage code to words |
| `fold` / `folds` | Present only on fold frames. This is the variant App Flow A3 introduced |
| `ping` | Every 5 seconds while a stage is slow. Carries no payload and shows nothing |
| `result` / `error` | Exactly one, terminal, nothing after it |

Fold frames carry both the stage `label` and the fold `label`, so a client that does not understand `fold` still renders a coherent line. That is deliberate redundancy: it lets the fold variant ship without a coordinated frontend release.

---

## 13. Query catalogue

Every query is a named file under `backend/app/db/queries/`, loaded at import, parameterised with `%(name)s`. No query is assembled from user input; where a column name must reach SQL, it comes from the parsed header allow-list (TRD §4).

| File | Purpose | Used by |
|---|---|---|
| `users_insert.sql` | Create an account | `/auth/signup` |
| `users_by_email.sql` | Login and reset lookup | `/auth/login`, `/auth/reset/request` |
| `users_by_google_sub.sql` | OAuth callback | `/auth/google/callback` |
| `users_set_password.sql` | Reset completion; also bumps `password_changed_at` | `/auth/reset/confirm` |
| `sessions_insert.sql` | New session on login | `/auth/login` |
| `sessions_by_hash.sql` | Every authenticated request | middleware |
| `sessions_delete.sql` / `sessions_delete_all_for_user.sql` | Logout, sign-out-everywhere | `/auth/logout`, password change |
| `sessions_delete_expired.sql` | Sweep | container start, login |
| `auth_tokens_insert.sql` / `auth_tokens_consume.sql` | Reset flow | `/auth/reset/*` |
| `analyses_insert.sql` | One transaction: analysis + checks + groups | stream `saving` stage |
| `narrative_insert.sql` / `narrative_by_analysis.sql` | The narrative, written after the metrics at the narration stage | stream `saving` (child write), report read |
| `analyses_by_id.sql` / `analyses_for_user.sql` | Report and history | `GET /analyses/{id}`, `/history` |
| `analyses_delete.sql` | Owner deletion | `DELETE /analyses/{id}` |
| `analyses_by_share_token.sql` | Share read path | `/shared/{token}` |
| `checks_by_analysis.sql` / `groups_by_analysis.sql` | Assembling `AnalysisResult` | every report read |
| `repairs_delete.sql` / `repairs_insert.sql` / `repairs_by_analysis.sql` | The three-strategy comparison: read for the report, replaced as a set on re-run | `GET /analyses/{id}`, `/analyses/{id}/repairs` |
| `chat_insert.sql` / `chat_by_analysis.sql` | Chat | `/analyses/{id}/chat` |
| `shares_insert.sql` / `shares_by_hash.sql` / `shares_delete.sql` / `shares_touch.sql` | Share lifecycle | `/analyses/{id}/shares`, `/shared/{token}` |
| `rate_limit_hit.sql` | The UPSERT counter | every limited endpoint |
| `rate_limits_sweep.sql` | Old windows | container start, login |
| `llm_cache_get.sql` / `llm_cache_put.sql` | Narrative and chat cache | `/analyses/{id}`, `/chat` |
| `account_export_counts.sql` | The counts shown in the delete dialog | `/account` |

Three of these carry a rule worth stating because a refactor can silently break it:

- **`analyses_for_user.sql` reads `top_level_analyses`**, never `analyses` directly. That is what keeps repair children nested instead of appearing as unrelated uploads (S4).
- **`analyses_insert.sql` is the only writer of `deciding_checks`**, and it takes the value from `verdict.py`'s return, not from a second computation in SQL.
- **`repairs_delete.sql` + `repairs_insert.sql` are one transaction.** There is no upsert, because the table is immutable (§7).

The account-deletion dialog reads its counts from `account_export_counts.sql` in one round trip rather than four — the categories it lists must be the categories that actually get deleted, and one query is the cheapest way to keep them honest.

---

## 14. Index rationale

Only indexes that exist for a named query. An index nobody uses is a write cost with no reader.

| Index | Serves | Why not covered by something else |
|---|---|---|
| `users_email_lower_uniq` | Login, signup duplicate check, reset lookup | The unique constraint is the index; a case-sensitive one would let `A@b.com` and `a@b.com` both exist |
| `users_google_sub_uniq` (partial) | OAuth callback | Partial because most rows are null and uniqueness must apply only where present |
| `sessions_user_idx` | Sign out everywhere | The primary key is on the token, not the user |
| `sessions_expiry_idx` | The sweep | A sweep by primary key would be a full scan |
| `analyses_user_created_idx` | History, newest first; also owner deletion | Composite because history is always filtered by user and ordered by date. `top_level_analyses` filters `parent_id is null` on top of this scan — the residual filter is cheap and does not justify a second index on the same prefix |
| `analyses_parent_idx` (partial) | Repair children and the parent cascade | Partial because only repair results have a parent |
| `analysis_repairs_recommended_idx` (partial) | "Which strategy was recommended" | At most one row per analysis, so a partial index stays tiny |
| `chat_messages_analysis_idx` | Loading a transcript | Ordered composite so the sort comes from the index |
| `shares_analysis_idx` | Listing links on the report page | The primary key is on the token, not the analysis |
| `rate_limits_window_idx` | Sweeping old windows | The primary key starts with `bucket`, which a time range cannot use |
| `llm_cache_analysis_idx` (partial) | Cascade and inspection | Partial because cache rows without an analysis are legal |

No index on `deciding_checks`: it is read as part of the row history already fetched, never filtered on.

---

## 15. What must never be stored

A checklist for review, because the promise is the product.

| Never stored | Where it would have leaked in |
|---|---|
| A cell value, a row, a column's distinct values | Nowhere. Enforced by review and by the shape test in §3.1 |
| The uploaded file, in any form including base64 | Nowhere. Parsing returns aggregates and drops the frame |
| A repaired dataset | Nowhere. Regenerated per download from the re-uploaded file (App Flow A6) |
| A raw IP address | `rate_limits.identifier` uses a peppered hash |
| A password, a session token, a reset token, a share token | Only SHA-256 digests reach the database |
| A reset or share token in a log line | A redaction filter plus a test (F8-AC4) |
| An OAuth access or refresh token | Nothing is stored after the callback; we ask for no offline access |
| A prompt that contains column names | Prompts are built at request time and never persisted |

---

## 16. Traceability

| Schema decision | Serves |
|---|---|
| Immutability triggers on `analyses`, `analysis_checks`, `analysis_groups`, `analysis_repairs` | PRD F3 "a result is immutable once stored", S3 traceability |
| `parent_id` + `repair_strategy` on `analyses` | F6 "a child analysis linked to it" |
| `top_level_analyses` view | F6 nesting, S4; the history filter cannot be dropped |
| `analysis_repairs` table | F9 "the chosen repair and its comparison", F6-AC4 |
| `source_sha256` | App Flow A6 fingerprint check |
| `analysis_narratives.kind` | F4-AC4 labelling template output |
| `chat_messages.citations` | F10 "cites only stored numbers" |
| `shares` with no revoked/expiry column | F7 revocation by deletion, F7-AC2 |
| `rate_limits.identifier` hashed | PRD §10 privacy table |
| `analysis_checks.reason` closed vocabulary | PRD §8.4 fixed reasons |
| `thresholds` jsonb on `analyses` | F3-AC3, §8.6 "one place" |
| `sampling` jsonb | F1-AC7 |
| Server-authored sentence fields | F4-AC6 |
| `deciding_checks` array + its constraints | PRD §8.5 precedence, F4-AC1; ties are named, not picked |
| `deciding_checks` consistency test | §3.3; the cache cannot drift from the check rows |
| Cascade rules + the ten-zero test | F9-AC1 |
| No row data anywhere | C3, F6-AC6, F7-AC3, PRD §10 |
| `columns` as names and types only | F5 technical view, the fingerprint check, the privacy claim |

---

*End of Backend Schema v2.2. The Implementation Plan is written and starts after day zero.*
