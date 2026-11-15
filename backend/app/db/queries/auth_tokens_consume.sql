-- auth_tokens_consume.sql
-- A token issued before the last password change is dead (F8-AC2).
update auth_tokens t
set used_at = now()
from users u
where u.id = t.user_id
  and t.token_hash = %(token_hash)s
  and t.used_at is null
  and t.expires_at > now()
  and t.created_at >= u.password_changed_at
returning t.token_hash, t.user_id, t.purpose, t.created_at, t.expires_at, t.used_at;
