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