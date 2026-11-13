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