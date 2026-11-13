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