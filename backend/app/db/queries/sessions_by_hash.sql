-- sessions_by_hash.sql
select token_hash, user_id, created_at, expires_at, last_seen_at
from sessions
where token_hash = %(token_hash)s;