create table shares (
  token_hash     text primary key,
  analysis_id    uuid not null references analyses(id) on delete cascade,
  created_at     timestamptz not null default now(),
  last_viewed_at timestamptz,
  view_count     integer not null default 0 check (view_count >= 0)
);

create index shares_analysis_idx on shares (analysis_id);