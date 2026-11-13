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