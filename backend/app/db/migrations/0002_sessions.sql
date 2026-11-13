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