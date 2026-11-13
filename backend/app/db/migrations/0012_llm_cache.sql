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