-- sessions_insert.sql
insert into sessions (token_hash, user_id, expires_at)
values (%(token_hash)s, %(user_id)s, %(expires_at)s)
returning token_hash, user_id, created_at, expires_at, last_seen_at;