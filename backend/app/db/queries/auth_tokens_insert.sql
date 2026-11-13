-- auth_tokens_insert.sql
insert into auth_tokens (token_hash, user_id, purpose, expires_at)
values (%(token_hash)s, %(user_id)s, %(purpose)s, %(expires_at)s)
returning token_hash, user_id, purpose, created_at, expires_at, used_at;