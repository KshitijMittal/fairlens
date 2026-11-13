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

  -- The exact AnalysisResult returned to the client (S8). The tables below and
  -- analysis_checks/analysis_groups are the queryable projection; this column is
  -- what a stored read returns, so a stored result cannot drift from a fresh one.
  result         jsonb not null,

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