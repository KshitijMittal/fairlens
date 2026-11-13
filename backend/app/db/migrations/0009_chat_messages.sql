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