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