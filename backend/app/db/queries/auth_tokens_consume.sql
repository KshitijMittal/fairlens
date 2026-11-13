-- auth_tokens_consume.sql
update auth_tokens
set used_at = now()
where token_hash = %(token_hash)s
  and used_at is null
  and expires_at > now()
returning token_hash, user_id, purpose, created_at, expires_at, used_at;